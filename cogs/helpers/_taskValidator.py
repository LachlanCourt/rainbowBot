import json


class Validator:
    def __init__():
        pass

    def validate(fileName):
        try:
            f = open(fileName)
            data = json.load(f)
            f.close()

            tasks = data["tasks"]
            days = {
                "00": "Sun",
                "01": "Mon",
                "02": "Tue",
                "03": "Wednes",
                "04": "Thurs",
                "05": "Fri",
                "06": "Satur",
                "*": "any day",
            }
            months = {
                "01": "January",
                "02": "February",
                "03": "March",
                "04": "April",
                "05": "May",
                "06": "June",
                "07": "July",
                "08": "August",
                "09": "September",
                "10": "October",
                "11": "November",
                "12": "December",
                "*": "any month",
            }

            out = ""
            for task in tasks:
                start = task[0].split()
                command = task[1]
                args = task[2]
                preposition = task[3]
                end = task[4].split()
                out += f"Execute command `{command} {args}` at {start[1] if start[1] != '*' else 'any month'}:{start[0] if start[0] != '*' else 'any day'}"
                out += f" on day {start[2] if start[2] != '*' else 'any'} of {months[start[3]]} if it is {days[start[4]]}day\n"

                if preposition == "until":
                    out += f"    Revert command `{command} {args}` at {end[1] if end[1] != '*' else 'any'}:{end[0] if end[0] != '*' else 'any'}"
                    out += f" on day {end[2] if end[2] != '*' else 'any day'} of {months[end[3]]} if it is {days[end[4]]}day\n\n"

                # Add custom EOL character to split on in output command
                out += chr(255)

            return (
                True,
                "File is valid. Tasks will run at the following times:\n'0'\n" + out,
            )
        except Exception as e:
            return False, "File is not valid. See below:\n'0'\n" + str(e)
