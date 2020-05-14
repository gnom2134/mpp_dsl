from mpp_interpreter import MPPInterpreter

if __name__ == '__main__':
    interpreter = MPPInterpreter()
    with open('album.mpp') as file:
        program = file.read()
    interpreter.run_program(program)
