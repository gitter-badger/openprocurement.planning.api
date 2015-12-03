from pyramid.events import ContextFound
from openprocurement.planning.api.design import add_design
from openprocurement.planning.api.utils import plan_from_data, extract_plan, set_logging_context


def includeme(config):
    print("init planing")
    # config planning couchdb database
    # server = config.registry.couchdb_server  # current database
    # db_name = config.registry.db.name  # main database name
    # db_name_plan = config.get_settings().get('couchdb.db_name_plan') if config.get_settings().get('couchdb.db_name_plan') else db_name + '_plan'  # planning database name - from config or with '_plan' suffix
    # # create additional database if does't exist
    # if db_name_plan not in server:
    #     server.create(db_name_plan)
    # db_plan = server[db_name_plan]
    # # add planning database to registry
    # config.registry.db_plan = db_plan

    add_design()
    config.add_subscriber(set_logging_context, ContextFound)
    config.add_request_method(extract_plan, 'plan', reify=True)
    config.add_request_method(plan_from_data)
    config.scan("openprocurement.planning.api.views")
