from os import path


def read_request(name: str) -> str:
    req_path = path.join('sql', name+'.sql')
    with open(req_path, mode='r') as file:
        return ''.join(file.readlines())


class SQLRequests:
    build_squadrons_current_data = read_request('build_squadrons_current_data')
    schema = read_request('schema')
    squad_deleted = read_request('squad_deleted')
    create_operation_id = read_request('create_operation_id')
    insert_info = read_request('insert_info')
    delete_squadron = read_request('delete_squadron')
    insert_news = read_request('insert_news')
