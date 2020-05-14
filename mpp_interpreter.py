import modules


class MPPInterpreter:
    def __init__(self):
        self.output = None
        self.input = None
        self.interpreter_commands = []
        self.tmp = None

    # returns function
    def out(self, args):
        if '-module' in args:
            if args['-module'] == 'docx':
                out_to = modules.DocxModule(args['argument'])
            else:
                out_to = None

            def result(x=None):
                self.output = out_to
        elif '-command' in args:
            if args['-command'] == 'write':
                text = args['argument']
            else:
                text = ''

            def result(x=None):
                if text == '__this__':
                    self.output.write(x)
                else:
                    self.output.write({'text': text})
        else:
            def result(x=None):
                pass

        return result

    # returns function
    def get(self, args):
        if '-module' in args:
            if args['-module'] == 'web':
                in_from = modules.WebModule(args['argument'])
            else:
                # wrong mode
                return -1
        else:
            in_from = None

        def result(x=None):
            self.input = in_from
            self.tmp = self.input.get()

        return result

    # returns function
    def loop(self, args, indices_of_commands):
        filter_tmp = self.parse_filter(args['argument'])

        def result(x=None):
            # every iterable object must have filter method
            for i in self.tmp.filter(filter_tmp):
                for j in indices_of_commands:
                    self.interpreter_commands[j](i)

        return result

    @staticmethod
    def parse_command(line):
        line = line.strip().split('#', 1)[0].strip()
        if len(line) == 0:
            # empty line
            return 0
        words = line.split()
        result = {
            'command': words[0],
            'argument': words[-1]
        }

        if len(words) % 2 != 0:
            # wrong number of arguments
            return -1

        for num in range(1, len(words) - 1, 2):
            flag = words[num]
            if not flag.startswith('-'):
                # no flag given
                return -2
            result[flag] = words[num + 1]

        return result

    @staticmethod
    def parse_filter(line):
        result = {}
        conditions = line.split('&&')
        for c in conditions:
            words = c.split('==')
            result[words[0]] = words[1]
        return result

    def run_program(self, text):
        commands = text.split('\n')
        commands = [x for x in commands if len(x.strip()) != 0]

        # class field for keeping instructions in case we need to use them again
        self.interpreter_commands = []

        # variable for storing loop data
        command_indices = [{'items': [], 'command_num': 0}]

        count = 0
        tabs = 0
        for command in commands:
            # counting tabs to see when the loop ends
            prev_tabs = tabs
            tabs = len(command) - len(command.lstrip('\t'))
            if tabs > prev_tabs:
                if tabs - prev_tabs > 1:
                    raise RuntimeError('wrong number of tabs on line ' + str(count))
            elif tabs < prev_tabs:
                for _ in range(prev_tabs - tabs):
                    self.interpreter_commands[command_indices[-1]['command_num']] = self.loop(
                        command_indices[-1]['args'],
                        command_indices[-1]['items']
                    )
                    command_indices.pop()

            command_indices[-1]['items'].append(count)

            # command parsing
            parsed_command = self.parse_command(command)

            # check for errors
            if parsed_command == -1:
                raise RuntimeError('wrong number of arguments given on line ' + str(count + 1))
            elif parsed_command == -2:
                raise RuntimeError('wrong flag given on line ' + str(count + 1))
            elif parsed_command == 0:
                raise RuntimeError('empty line ' + str(count + 1))

            # searching for command's type
            if parsed_command['command'] == 'out':
                self.interpreter_commands.append(self.out(parsed_command))
            elif parsed_command['command'] == 'get':
                self.interpreter_commands.append(self.get(parsed_command))
            elif parsed_command['command'] == 'loop_by_tmp':
                command_indices.append({'args': parsed_command, 'command_num': count, 'items': []})
                self.interpreter_commands.append(None)
            else:
                raise RuntimeError('wrong command given on line ' + str(count + 1))

            count += 1

        # filling last loop's commands
        for _ in range(tabs):
            self.interpreter_commands[command_indices[-1]['command_num']] = self.loop(
                command_indices[-1]['args'],
                command_indices[-1]['items']
            )
            command_indices.pop()

        # running outer loop of instructions
        for index in command_indices[0]['items']:
            self.interpreter_commands[index](self.tmp)
