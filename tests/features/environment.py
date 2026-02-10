from backend.database import init_db

def before_all(context):
    """Se ejecuta una vez antes de todos los tests"""
    init_db()

def before_scenario(context, scenario):
    """Resetea el estado antes de cada escenario"""
    context.response = None
    context.api_status = False