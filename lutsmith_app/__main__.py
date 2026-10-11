import multiprocessing
import sys

if __name__ == '__main__':
    multiprocessing.freeze_support()             # the packaged app also runs the helper processes of the turns
    from lutsmith_app.main import main
    sys.exit(main())
