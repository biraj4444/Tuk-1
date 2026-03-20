import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from driver_portal.app import app

if __name__ == "__main__":
    app.run()
