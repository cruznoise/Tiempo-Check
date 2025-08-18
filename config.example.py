import os

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "mysql+mysqlconnector://root:base@localhost/tiempocheck_db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False


    TZ = os.getenv("TZ", "America/Mexico_City")

    JOB_FH_MINUTES = int(os.getenv("JOB_FH_MINUTES", "1"))   
    JOB_CLOSE_HOUR = int(os.getenv("JOB_CLOSE_HOUR", "0"))      
    JOB_CLOSE_MINUTE = int(os.getenv("JOB_CLOSE_MINUTE", "5")) 
    JOB_CATCHUP_HOURS = int(os.getenv("JOB_CATCHUP_HOURS", "1"))
    JOB_CATCHUP_LOOKBACK = int(os.getenv("JOB_CATCHUP_LOOKBACK", "3"))  
