from flask import Blueprint, render_template, request
from flask_login import current_user

from lib.omw_sql import fetch_ili, f_rate_summary, fetch_src, fetch_kind, fetch_status, query_omw
from lib.wn_syntax import uploadFile, validateFile
from omw.blueprints.ili.forms import SearchILIForm
from omw.blueprints.user.decorator import login_required

ili = Blueprint('ili', __name__, template_folder='templates')


@ili.route('/ili', methods=['GET', 'POST'])
def ili_welcome():
    return render_template('ili/ili_welcome.html')


@ili.route('/ili/concepts/<c>', methods=['GET', 'POST'])
def concepts_ili(c=None):
    c = c.split(',')
    ili, ili_defs = fetch_ili(c)
    rsumm, up_who, down_who = f_rate_summary(list(ili.keys()))

    return render_template('concept-list.html', ili=ili,
                           rsumm=rsumm, up_who=up_who, down_who=down_who)


@ili.route('/ili/search', methods=['GET', 'POST'])
@ili.route('/ili/search/<q>', methods=['GET', 'POST'])
def search_ili(q=None):

    form = SearchILIForm()

    if q:
        query = q
    else:
        query = request.form.get('query')

    src_id = fetch_src()
    kind_id = fetch_kind()
    status_id = fetch_status()

    ili = dict()
    for c in query_omw("""SELECT * FROM ili WHERE def GLOB ?
                             """, [query]):
        ili[c['id']] = (kind_id[c['kind_id']], c['def'],
                        src_id[c['origin_src_id']], c['src_key'],
                        status_id[c['status_id']], c['superseded_by_id'],
                        c['t'])

    rsumm, up_who, down_who = f_rate_summary(list(ili.keys()))
    return render_template('concept-list.html', ili=ili,
                           rsumm=rsumm, up_who=up_who, down_who=down_who)


@ili.route('/ili/validation-report', methods=['GET', 'POST'])
@login_required(role=0, group='open')
def validation_report():
    vr, filename, wn, wn_dtls = validateFile(current_user.id)

    return render_template('validation-report.html',
                           vr=vr, wn=wn, wn_dtls=wn_dtls,
                           filename=filename)


@ili.route('/ili/report', methods=['GET', 'POST'])
@login_required(role=0, group='open')
def report():
    passed, filename = uploadFile(current_user.id)
    return render_template('report.html',
                           passed=passed,
                           filename=filename)
