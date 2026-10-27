from launcher_gui import main
import sys

if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == '--smoke-test':
        from smoke_check import run
        run(sys.argv[2])
    else:
        main()
