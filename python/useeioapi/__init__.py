import os
import useeioapi.data as data

from flask import Flask, jsonify, request, abort

app = Flask(__name__)
models = {}
data_dir = 'data'


# no caching -> just for dev ...
@app.after_request
def add_header(r):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    r.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    r.headers['Pragma'] = 'no-cache'
    r.headers['Expires'] = '0'
    r.headers['Cache-Control'] = 'public, max-age=0'
    return r


@app.route('/api/models')
def get_models():
    infos = data.read_model_infos(data_dir)
    return jsonify(infos)


@app.route('/api/<model>/demands')
def get_demands(model: str):
    demands = data.read_demand_infos(data_dir, model)
    return jsonify(demands)


@app.route('/api/<model>/demands/<demand_id>')
def get_demand(model: str, demand_id: str):
    demands = data.read_demand_infos(data_dir, model)
    for demand in demands:
        did = demand.get('id')
        if did == demand_id:
            return jsonify(demand)
    return abort(404)


@app.route('/api/<model>/sectors')
def get_sectors(model: str):
    sectors = data.read_sectors(data_dir, model)
    return jsonify(sectors)


@app.route('/api/<model>/sectors/<path:sector_id>')
def get_sector(model: str, sector_id: str):
    sectors = data.read_sectors(data_dir, model)
    for s in sectors:
        if s.get('id') == sector_id:
            return jsonify(s)
    abort(404)


@app.route('/api/<model>/flows')
def get_flows(model: str):
    flows = data.read_flows(data_dir, model)
    return jsonify(flows)


@app.route('/api/<model>/flows/<path:flow_id>')
def get_flow(model: str, flow_id: str):
    flows = data.read_flows(data_dir, model)
    for flow in flows:
        if flow.get('id') == flow_id:
            return jsonify(flow)
    abort(404)


@app.route('/api/<model>/indicators')
def get_indicators(model: str):
    m = models.get(model)  # type: data.Model
    if m is None:
        abort(404)
    l = []
    for i in m.indicators:
        l.append(i.as_json_dict())
    return jsonify(l)


@app.route('/api/<model>/calculate', methods=['POST'])
def calculate(model: str):
    m = models.get(model)  # type: data.Model
    if m is None:
        abort(404)
    demand = request.get_json()
    result = m.calculate(demand)
    return jsonify(result)


@app.route('/api/<model>/matrix/<name>')
def get_matrix(model: str, name: str):
    m = models.get(model)  # type: data.Model
    if m is None:
        abort(404)
    if name in ('A', 'B', 'C', 'D', 'L', 'U'):
        return __get_numeric_matrix(m, name)
    elif name in ('B_dqi', 'D_dqi', 'U_dqi'):
        return __get_dqi_matrix(m, name)
    else:
        abort(404)


def __get_numeric_matrix(m: data.Model, name: str):
    mat = m.get_matrix(name)
    if mat is None:
        abort(404)
    col = __get_index_param('col', mat.shape[1])
    if col >= 0:
        return jsonify(mat[:, col].tolist())
    row = __get_index_param('row', mat.shape[0])
    if row >= 0:
        return jsonify(mat[row, :].tolist())
    return jsonify(mat.tolist())


def __get_dqi_matrix(m: data.Model, name: str):
    mat = m.get_dqi_matrix(name)
    if mat is None:
        abort(404)
    if len(mat) == 0:
        abort(404)
    col = __get_index_param('col', len(mat[0]))
    if col >= 0:
        vals = [row[col] for row in mat]
        return jsonify(vals)
    row = __get_index_param('row', len(mat))
    if row >= 0:
        return jsonify(mat[row])
    return jsonify(mat)


def __get_index_param(name: str, size: int) -> int:
    val = request.args.get(name)
    if val is None or len(val) == 0:
        return -1
    try:
        idx = int(val)
        if idx >= size:
            abort(400)
        return idx
    except:
        abort(400)


def serve(data_folder: str, port='5000'):
    global data_dir, app
    data_dir = data_folder
    for name in os.listdir(data_folder):
        f = os.path.join(data_folder, name)
        if os.path.isdir(f):
            pass
            # TODO: check model folder (all data present etc.)
            # model = Model(f, name)
            # models[name] = model
    app.run('0.0.0.0', port)
