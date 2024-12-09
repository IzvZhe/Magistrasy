import psycopg2
import xml.etree.ElementTree as ET

import psycopg2

class FuzzySystemDatabase:
    def __init__(self, DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT):
        self.DB_NAME = DB_NAME
        self.DB_USER = DB_USER
        self.DB_PASSWORD = DB_PASSWORD
        self.DB_HOST = DB_HOST
        self.DB_PORT = DB_PORT

    def Get_file(self, system_name):
        data = []

        knowledge_base = self.Get_knowledge_base(system_name)
        mamdani_rule_base = self.Get_mamdani_rule_base(system_name)

        data.append(knowledge_base)
        data.append(mamdani_rule_base)

        return self.Create_fuzzy_system_xml(data)

    def Get_knowledge_base(self, system_name):
        results = {
            "system_name": system_name,
            "network_address": "",
            "variables": []
        }
        connection = None
        cursor = None

        try:
            connection = psycopg2.connect(
                dbname=self.DB_NAME,
                user=self.DB_USER,
                password=self.DB_PASSWORD,
                host=self.DB_HOST,
                port=self.DB_PORT
            )

            cursor = connection.cursor()

            query = '''
            SELECT 
                sys."Name" AS system_name, 
                sys."NetworkAdress" AS network_address,
                var."Name" AS variable_name, 
                var."Domainleft" AS domain_left, 
                var."Domainright" AS domain_right, 
                var."Scale" AS scale, 
                var."DefaultValue" AS default_value, 
                var."Accumulation" AS accumulation, 
                var."Defuzzifier" AS defuzzifier, 
                var."Type" AS type,
                ter."Name" AS term_name, 
                ter."Complament" AS complement,
                ter."Param1" AS param1, 
                ter."Param2" AS param2,
                ter."Param3" AS param3,
                ter."Param4" AS param4, 
                ter."Shape" AS shape
            FROM 
                "Fuzzy systems" AS sys
            JOIN 
                "Fuzzy variables" AS var
            ON 
                sys."ID" = var."System_ID"
            JOIN 
                "Fuzzy terms" AS ter
            ON 
                var."ID" = ter."Variables_ID"
            WHERE
                sys."Name" = %s;
            '''

            cursor.execute(query, (system_name,))
            rows = cursor.fetchall()

            if rows:
                results["network_address"] = rows[0][1]

                variable_dict = {}
                for row in rows:
                    variable_name = row[2]
                    
                    if variable_name not in variable_dict:
                        variable_dict[variable_name] = {
                            "accumulation": row[7],
                            "complement": row[11],
                            "default_value": row[6],
                            "defuzzifier": row[8],
                            "domain_left": row[3],
                            "domain_right": row[4],
                            "param1": row[12],
                            "param2": row[13],
                            "param3": row[14],
                            "param4": row[15],
                            "scale": row[5],
                            "shape": row[16],
                            "type": row[9],
                            "variable_name": variable_name,
                            "terms": []
                        }
                    
                    variable_dict[variable_name]["terms"].append({
                        "term_name": row[10],
                        "complement": row[11],
                        "param1": row[12],
                        "param2": row[13],
                        "param3": row[14],
                        "param4": row[15],
                        "shape": row[16],
                    })

                for variable in variable_dict.values():
                    variable["terms"] = variable_dict[variable["variable_name"]]["terms"]
                    results["variables"].append(variable)

        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

        return results

    def Get_mamdani_rule_base(self, system_name):
        results = {
            "mrb_name": "",
            "and_method": "",
            "or_method": "",
            "activation_method": "",
            "rules": []
        }
        connection = None
        cursor = None

        try:
            connection = psycopg2.connect(
                dbname=self.DB_NAME,
                user=self.DB_USER,
                password=self.DB_PASSWORD,
                host=self.DB_HOST,
                port=self.DB_PORT
            )

            cursor = connection.cursor()

            query = '''
            SELECT 
                mrb."Name" AS mrb_name,
                mrb."andMethod" AS and_method, 
                mrb."orMethod" AS or_method, 
                mrb."activationMethod" AS activation_method,
                rul."Name" AS rule_name, 
                rul."Connector" AS connector, 
                rul."orMethod" AS rule_or_method,
                rul."Weight" AS weight, 
                rul."andMethod" AS rule_and_method, 
                rul."Antecedent terms" AS antecedent_terms, 
                rul."Antecedent variables" AS antecedent_variables, 
                rul."Antecedent modifiers" AS antecedent_modifiers, 
                rul."Consequent Variables" AS consequent_variables, 
                rul."Consequent Terms" AS consequent_terms
            FROM 
                "Fuzzy systems" AS sys
            JOIN 
                "Mamdani Rules Base" AS mrb
            ON 
                sys."ID" = mrb."System_ID"
            JOIN 
                "Rules" AS rul
            ON 
                mrb."ID" = rul."MRB_ID"
            WHERE
                sys."Name" = %s;
            '''

            cursor.execute(query, (system_name,))
            rows = cursor.fetchall()

            if rows:
                results["mrb_name"] = rows[0][0]
                results["and_method"] = rows[0][1]
                results["or_method"] = rows[0][2]
                results["activation_method"] = rows[0][3]

                for row in rows:
                    results["rules"].append({
                        "rule_name": row[4],
                        "connector": row[5],
                        "rule_or_method": row[6],
                        "weight": row[7],
                        "antecedent_terms": row[9],  
                        "antecedent_variables": row[10],  
                        "antecedent_modifiers": row[11] if row[11] else [None],  
                        "consequent_terms": row[13], 
                        "consequent_variables": row[12]
                    })

        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

        return results

    def Create_fuzzy_system_xml(self, data):
        if not isinstance(data, list) or len(data) != 2:
            raise ValueError("data must be a list containing two dictionaries")

        knowledge_base_data = data[0]
        mamdani_rule_base_data = data[1] 

        required_kb_keys = ["system_name", "network_address", "variables"]
        for key in required_kb_keys:
            if key not in knowledge_base_data:
                raise KeyError(f"Missing key in knowledge base data: {key}")

        required_mrb_keys = ["mrb_name", "and_method", "or_method", "activation_method", "rules"]
        for key in required_mrb_keys:
            if key not in mamdani_rule_base_data:
                raise KeyError(f"Missing key in Mamdani rule base data: {key}")

        fuzzy_system = ET.Element("fuzzySystem", attrib={
            "name": knowledge_base_data["system_name"],
            "networkAddress": knowledge_base_data["network_address"]
        })
        
        knowledge_base = ET.SubElement(fuzzy_system, "knowledgeBase")

        for var in knowledge_base_data["variables"]:
            fuzzy_variable = ET.SubElement(knowledge_base, "fuzzyVariable", attrib={
                "name": var["variable_name"],
                "domainleft": str(var["domain_left"]),
                "domainright": str(var["domain_right"]),
                "scale": var.get("scale", ""),
                "type": var["type"]
            })

            for term in var["terms"]:
                fuzzy_term = ET.SubElement(fuzzy_variable, "fuzzyTerm", attrib={
                    "name": term["term_name"],
                    "complement": str(term.get("complement", False)).lower()
                })

                shape_element = ET.SubElement(fuzzy_term, term["shape"], {
                    "param1": str(term.get("param1", "")),
                    "param2": str(term.get("param2", "")),
                    "param3": str(term.get("param3", "")),
                    "param4": str(term.get("param4", ""))
                })
            
        mamdani_rule_base = ET.SubElement(fuzzy_system, "mamdaniRuleBase", attrib={
            "name": mamdani_rule_base_data["mrb_name"],
            "andMethod": mamdani_rule_base_data["and_method"],
            "orMethod": mamdani_rule_base_data["or_method"],
            "activationMethod": mamdani_rule_base_data["activation_method"]
        })

        for rule in mamdani_rule_base_data["rules"]:
            rule_element = ET.SubElement(mamdani_rule_base, "rule", attrib={
                "name": rule["rule_name"],
                "connector": rule["connector"],
                "orMethod": rule.get("rule_or_method", ""),
                "weight": str(rule.get("weight", 1.0))
            })

            antecedent = ET.SubElement(rule_element, "antecedent")
            for idx, term in enumerate(rule["antecedent_terms"]):
                clause = ET.SubElement(antecedent, "clause")
                variable = ET.SubElement(clause, "variable")
                variable.text = rule["antecedent_variables"][idx]
                term_element = ET.SubElement(clause, "term")
                term_element.text = term
                
                if rule["antecedent_modifiers"][idx]:
                    clause.set("modifier", rule["antecedent_modifiers"][idx])

            consequent = ET.SubElement(rule_element, "consequent")
            then_clause = ET.SubElement(consequent, "then")
            for idx, term in enumerate(rule["consequent_terms"]):
                clause = ET.SubElement(then_clause, "clause")
                variable = ET.SubElement(clause, "variable")
                variable.text = rule["consequent_variables"][idx]
                term_element = ET.SubElement(clause, "term")
                term_element.text = term

        return ET.tostring(fuzzy_system, encoding="utf-8").decode("utf-8")

def Get_List(DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT):
    names_list = []

    connection = None
    cursor = None

    try:
        connection = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )

        cursor = connection.cursor()

        cursor.execute('SELECT "Name" FROM "Fuzzy systems";')

        names = cursor.fetchall()

        for name in names:
            names_list.append(name[0])

    except Exception as e:
        print(f"Произошла ошибка: {e}")

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

    return names_list

def Delete_all_data(DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT):
    try:
        connection = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )

        cursor = connection.cursor()

        delete_fuzzy_systems_query = 'DELETE FROM public."Fuzzy systems";'

        cursor.execute(delete_fuzzy_systems_query)
        
        connection.commit()
        print("All data deleted successfully!")

    except Exception as e:
        print(f"Error occurred while deleting data: {e}")
        return False

    finally:
        cursor.close()
        connection.close()

    return True

def Delete_one_data(DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, system_name):
    try:
        connection = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )

        cursor = connection.cursor()

        delete_fuzzy_systems_query = 'DELETE FROM public."Fuzzy systems" WHERE "Name" = %s;'
        cursor.execute(delete_fuzzy_systems_query, (system_name,))

        connection.commit()
        print(f"Record '{system_name}' deleted successfully!")

    except Exception as e:
        print(f"Error occurred while deleting data: {e}")
        return False

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

    return True

class FuzzySystemParser:
    def __init__(self, xml_file):
        self.xml_file = xml_file

    def parse_xml(self):
        tree = ET.parse(self.xml_file)
        root = tree.getroot()

        system_name = root.attrib['name']
        network_address = root.attrib['networkAddress']

        return system_name, network_address

    def get_fuzzy_variables(self, root):
        fuzzy_variables = []
        knowledge_base = root.find('knowledgeBase')

        for fuzzy_variable in knowledge_base.findall('fuzzyVariable'):
            var_name = fuzzy_variable.attrib['name']
            domain_left = float(fuzzy_variable.attrib['domainleft'])
            domain_right = float(fuzzy_variable.attrib['domainright'])
            scale = fuzzy_variable.attrib.get('scale', '')
            default_value = float(fuzzy_variable.attrib.get('defaultValue', 0.0))
            accumulation = fuzzy_variable.attrib.get('accumulation', '')
            defuzzifier = fuzzy_variable.attrib.get('defuzzifier', '')
            var_type = fuzzy_variable.attrib['type']

            fuzzy_variables.append({
                "name": var_name, 
                "domain_left": domain_left, 
                "domain_right": domain_right, 
                "scale": scale, 
                "default_value": default_value, 
                "accumulation": accumulation, 
                "defuzzifier": defuzzifier, 
                "type": var_type, 
                "terms": self.get_fuzzy_terms(root),
                "MRB": self.get_mamdani_rules_base(root),
                "Rule": self.get_rules(root)
            })

        return fuzzy_variables

    def get_fuzzy_terms(self, root):
        fuzzy_terms = []

        for fuzzy_term in root.findall('.//fuzzyTerm'):
            term_name = fuzzy_term.attrib['name']
            complement = fuzzy_term.attrib['complement'] == 'true'

            shape = None
            params = [None, None, None, None]

            if fuzzy_term.find('leftLinearShape') is not None:
                shape = 'leftLinearShape'
                shape_element = fuzzy_term.find('leftLinearShape')
                params[0] = shape_element.attrib['param1']
                params[1] = shape_element.attrib['param2']

            elif fuzzy_term.find('triangularShape') is not None:
                shape = 'triangularShape'
                shape_element = fuzzy_term.find('triangularShape')
                params[0] = shape_element.attrib['param1']
                params[1] = shape_element.attrib['param2']
                params[2] = shape_element.attrib['param3']

            elif fuzzy_term.find('leftGaussianShape') is not None:
                shape = 'leftGaussianShape'
                shape_element = fuzzy_term.find('leftGaussianShape')
                params[0] = shape_element.attrib['param1']
                params[1] = shape_element.attrib['param2']

            elif fuzzy_term.find('piShape') is not None:
                shape = 'piShape'
                shape_element = fuzzy_term.find('piShape')
                params[0] = shape_element.attrib['param1']
                params[1] = shape_element.attrib['param2']

            elif fuzzy_term.find('rightGaussianShape') is not None:
                shape = 'rightGaussianShape'
                shape_element = fuzzy_term.find('rightGaussianShape')
                params[0] = shape_element.attrib['param1']
                params[1] = shape_element.attrib['param2']

            elif fuzzy_term.find('trapezoidShape') is not None:
                shape = 'trapezoidShape'
                shape_element = fuzzy_term.find('trapezoidShape')
                params[0] = shape_element.attrib['Param1']
                params[1] = shape_element.attrib['Param2']
                params[2] = shape_element.attrib['Param3']
                params[3] = shape_element.attrib['Param4']

            fuzzy_terms.append({
                "name": term_name,
                "complement": complement,
                "shape": shape,
                "params": params
            })

        return fuzzy_terms

    def insert_into_db(self, DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, system_name, network_address, fuzzy_variables):
        try:
            conn = psycopg2.connect(
                dbname=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD,
                host=DB_HOST,
                port=DB_PORT
            )
            cursor = conn.cursor()

            insert_system_query = '''
            INSERT INTO public."Fuzzy systems" ("Name", "NetworkAdress")
            VALUES (%s, %s) RETURNING "ID"
            '''
            cursor.execute(insert_system_query, (system_name, network_address))
            system_id = cursor.fetchone()[0]

            insert_variable_query = '''
            INSERT INTO public."Fuzzy variables" ("Name", "Domainleft", "Domainright", "Scale", "DefaultValue", "Accumulation", "Defuzzifier", "Type", "System_ID")
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING "ID"
            '''
            insert_terms_query = '''
            INSERT INTO public."Fuzzy terms" ("Name", "Complament", "Param1", "Param2", "Param3", "Param4", "Variables_ID", "Shape")
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            '''
            insert_MRB_query = '''
            INSERT INTO public."Mamdani Rules Base" ("Name", "andMethod", "orMethod", "activationMethod", "System_ID")
            VALUES (%s, %s, %s, %s, %s) RETURNING "ID"
            '''
            insert_rule_query = '''
            INSERT INTO public."Rules" ("Name", "Connector", "orMethod", "Weight", "andMethod", "MRB_ID", "Antecedent terms", "Antecedent variables", "Antecedent modifiers", "Consequent Variables", "Consequent Terms")
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            '''

            for variable in fuzzy_variables:
                cursor.execute(insert_variable_query, (
                    variable['name'], 
                    variable['domain_left'], 
                    variable['domain_right'], 
                    variable['scale'], 
                    variable['default_value'], 
                    variable['accumulation'], 
                    variable['defuzzifier'], 
                    variable['type'], 
                    system_id
                ))
                variable_id = cursor.fetchone()[0]  ##

            for term in variable['terms']:
                cursor.execute(insert_terms_query, (
                    term['name'], 
                    term['complement'], 
                    term['params'][0], 
                    term['params'][1], 
                    term['params'][2], 
                    term['params'][3], 
                    variable_id, 
                    term['shape']
                ))


            for MRB in variable['MRB']:
                cursor.execute(insert_MRB_query, (
                    MRB['name'], 
                    MRB['andMethod'], 
                    MRB['orMethod'], 
                    MRB['activationMethod'], 
                    system_id
                ))
                MRB_id = cursor.fetchone()[0]

            for Rule in variable['Rule']:
                cursor.execute(insert_rule_query, (
                    Rule['name'], 
                    Rule['connector'], 
                    Rule['orMethod'], 
                    Rule['weight'], 
                    Rule['andMethod'], 
                    MRB_id,
                    Rule['antecedent terms'],
                    Rule['antecedent variables'],
                    Rule['antecedent modifiers'],
                    Rule['consequent variables'],
                    Rule['consequent terms']
                ))

            conn.commit()
            print("Data inserted successfully!")

        except Exception as e:
            print(f"Error occurred: {e}")

        finally:
            cursor.close()
            conn.close()

    def get_mamdani_rules_base(self, root):
        mamdani_rules_base = []

        for mamdani_rule_base in root.findall('mamdaniRuleBase'):
            name = mamdani_rule_base.attrib['name']
            and_method = mamdani_rule_base.attrib['andMethod']
            or_method = mamdani_rule_base.attrib['orMethod']
            activation_method = mamdani_rule_base.attrib['activationMethod']

            mamdani_rules_base.append({
                "name": name,
                "andMethod": and_method,
                "orMethod": or_method,
                "activationMethod": activation_method
            })
        
        return mamdani_rules_base

    def get_rules(self, root):
        rules_data = []

        for rule in root.findall('.//rule'):
            rule_name = rule.attrib.get('name')
            connector = rule.attrib.get('connector')
            or_method = rule.attrib.get('orMethod')
            weight = float(rule.attrib.get('weight'))
            and_method = rule.attrib.get('andMethod')

            antecedent_terms = []
            antecedent_variables = []
            antecedent_modifiers = []
            consequent_variables = []
            consequent_terms = []

            antecedent = rule.find('antecedent')
            if antecedent is not None:
                for clause in antecedent.findall('clause'):
                    variable = clause.find('variable').text
                    term = clause.find('term').text
                    antecedent_variables.append(variable)
                    antecedent_terms.append(term)

                    modifier = clause.attrib.get('modifier')
                    antecedent_modifiers.append(modifier if modifier else None)

            consequent = rule.find('consequent')
            if consequent is not None:
                for then_clause in consequent.find('then').findall('clause'):
                    variable = then_clause.find('variable').text
                    term = then_clause.find('term').text
                    consequent_variables.append(variable)
                    consequent_terms.append(term)

            rule_info = {
                "name": rule_name,
                "connector": connector,
                "orMethod": or_method,
                "weight": weight,
                "andMethod": and_method,
                "antecedent terms": antecedent_terms,
                "antecedent variables": antecedent_variables,
                "antecedent modifiers": antecedent_modifiers,
                "consequent variables": consequent_variables,
                "consequent terms": consequent_terms
            }

            rules_data.append(rule_info)

        return rules_data


    def Put_fml_file(self, DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT):
        system_name, network_address = self.parse_xml()
        tree = ET.parse(self.xml_file)
        root = tree.getroot()

        fuzzy_variables = self.get_fuzzy_variables(root)

        self.insert_into_db(DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, system_name, network_address, fuzzy_variables)


