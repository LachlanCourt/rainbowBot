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
                "0": "Sun",
                "1": "Mon",
                "2": "Tue",
                "3": "Wednes",
                "4": "Thurs",
                "5": "Fri",
                "6": "Satur",
                "*": "any ",
            }
            months = {
                "1": "January",
                "2": "February",
                "3": "March",
                "4": "April",
                "5": "May",
                "6": "June",
                "7": "July",
                "8": "August",
                "9": "September",
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
                out += f"Execute command `{command} {args}` at {start[1].zfill(2) if start[1] != '*' else 'any'}:{start[0].zfill(2) if start[0] != '*' else 'any'}"
                out += f" on day {start[2].zfill(2) if start[2] != '*' else 'any'} of {months[start[3]]} if it is {days[start[4]]}day\n"

                if preposition == "until":
                    out += f"    Revert command `{command} {args}` at {end[1].zfill(2) if end[1] != '*' else 'any'}:{end[0].zfill(2) if end[0] != '*' else 'any'}"
                    out += f" on day {end[2].zfill(2) if end[2] != '*' else 'any'} of {months[end[3]]} if it is {days[end[4]]}day\n\n"

                # Add custom EOL character to split on in output command
                out += chr(255)

            return (
                True,
                "File is valid. Tasks will run at the following times:\n\n" + out,
            )
        except Exception as e:
            return False, "File is not valid. See below:\n\n" + str(e)
