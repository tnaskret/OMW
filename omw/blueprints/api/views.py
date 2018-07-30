from flask import (
    Blueprint, request, render_template, jsonify)
from flask_login import current_user
from markupsafe import Markup

from lib.wn_syntax import validateFile, fetch_src_for_s_id, fetch_src_meta, fetch_labels, fetch_forms, fetch_sense, \
    fetch_pos, fetch_langs, fetch_id_from_userid, rate_ili_id, f_rate_summary, comment_ili_id, fetch_rate_id, \
    fetch_comment_id, fetch_allusers, confirmUpload, updateLabels, insert_new_project, insert_new_language, fetch_proj, \
    fetch_src, f_ss_id_by_ili_id, fetch_ss_basic, fetch_ssrel
from omw.blueprints.user.decorator import login_required

api = Blueprint('api', __name__, template_folder='templates')


@api.route('/_thumb_up_id')
def thumb_up_id():
    user = fetch_id_from_userid(current_user.id)
    ili_id = request.args.get('ili_id', None)
    rate = 1
    r = rate_ili_id(ili_id, rate, user)

    counts, up_who, down_who = f_rate_summary([ili_id])
    html = """ <span style="color:green" title="{}">+{}</span><br>
                   <span style="color:red"  title="{}">-{}</span>
               """.format(up_who[int(ili_id)], counts[int(ili_id)]['up'],
                          down_who[int(ili_id)], counts[int(ili_id)]['down'])
    return jsonify(result=html)


@api.route('/_thumb_down_id')
def thumb_down_id():
    user = fetch_id_from_userid(current_user.id)
    ili_id = request.args.get('ili_id', None)
    rate = -1
    r = rate_ili_id(ili_id, rate, user)

    counts, up_who, down_who = f_rate_summary([ili_id])
    html = """ <span style="color:green" title="{}">+{}</span><br>
                   <span style="color:red"  title="{}">-{}</span>
               """.format(up_who[int(ili_id)], counts[int(ili_id)]['up'],
                          down_who[int(ili_id)], counts[int(ili_id)]['down'])
    return jsonify(result=html)


@api.route('/_comment_id')
def comment_id():
    user = fetch_id_from_userid(current_user.id)
    ili_id = request.args.get('ili_id', None)
    comment = request.args.get('comment', None)
    comment = str(Markup.escape(comment))
    dbinsert = comment_ili_id(ili_id, comment, user)
    return jsonify(result=dbinsert)


@api.route('/_detailed_id')
def detailed_id():
    ili_id = request.args.get('ili_id', None)
    rate_hist = fetch_rate_id([ili_id])
    comm_hist = fetch_comment_id([ili_id])
    users = fetch_allusers()

    r_html = ""
    for r, u, t in rate_hist[int(ili_id)]:
        r_html += '{} ({}): {} <br>'.format(users[u]['userID'], t, r)

    c_html = ""
    for c, u, t in comm_hist[int(ili_id)]:
        c_html += '{} ({}): {} <br>'.format(users[u]['userID'], t, c)

    html = """
        <td colspan="9">
        <div style="width: 49%; float:left;">
        <h6>Ratings</h6>
        {}</div>
        <div style="width: 49%; float:right;">
        <h6>Comments</h6>
        {}</div>
        </td>""".format(r_html, c_html)

    return jsonify(result=html)


@api.route('/_confirm_wn_upload')
def confirm_wn_upload_id():
    user = fetch_id_from_userid(current_user.id)
    fn = request.args.get('fn', None)
    upload = confirmUpload(fn, user)
    labels = updateLabels()
    return jsonify(result=upload)


@api.route('/_add_new_project')
def add_new_project():
    user = fetch_id_from_userid(current_user.id)
    proj = request.args.get('proj_code', None)
    proj = str(Markup.escape(proj))
    if user and proj:
        dbinsert = insert_new_project(proj, user)
        return jsonify(result=dbinsert)
    else:
        return jsonify(result=False)


@api.route("/_load_lang_selector", methods=["GET"])
def omw_lang_selector():
    selected_lang = request.cookies.get('selected_lang')
    selected_lang2 = request.cookies.get('selected_lang2')
    lang_id, lang_code = fetch_langs()
    html = '<select name="lang" style="font-size: 85%; width: 9em" required>'
    for lid in lang_id.keys():
        if selected_lang == str(lid):
            html += """<option value="{}" selected>{}</option>
                        """.format(lid, lang_id[lid][1])
        else:
            html += """<option value="{}">{}</option>
                        """.format(lid, lang_id[lid][1])
    html += '</select>'
    html += '<select name="lang2" style="font-size: 85%; width: 9em" required>'
    for lid in lang_id.keys():
        if selected_lang2 == str(lid):
            html += """<option value="{}" selected>{}</option>
                        """.format(lid, lang_id[lid][1])
        else:
            html += """<option value="{}">{}</option>
                        """.format(lid, lang_id[lid][1])
    html += '</select>'
    return jsonify(result=html)


@api.route('/_add_new_language')
def add_new_language():
    user = fetch_id_from_userid(current_user.id)
    bcp = request.args.get('bcp', None)
    bcp = str(Markup.escape(bcp))
    iso = request.args.get('iso', None)
    iso = str(Markup.escape(iso))
    name = request.args.get('name', None)
    name = str(Markup.escape(name))
    if bcp and name:
        dbinsert = insert_new_language(bcp, iso, name, user)
        return jsonify(result=dbinsert)
    else:
        return jsonify(result=False)


@api.route('/_load_proj_details')
def load_proj_details():
    proj_id = request.args.get('proj', 0)
    if proj_id:
        proj_id = int(proj_id)
    else:
        proj_id = None

    projs = fetch_proj()
    srcs = fetch_src()
    srcs_meta = fetch_src_meta()

    html = str()

    if proj_id:
        i = 0
        for src_id in srcs.keys():

            if srcs[src_id][0] == projs[proj_id]:
                i += 1
                html += "<br><p><b>Source {}: {}-{}</b></p>".format(i,
                                                                    projs[proj_id], srcs[src_id][1])

                for attr, val in srcs_meta[src_id].items():
                    html += "<p style='margin-left: 40px'>"
                    html += attr + ": " + val
                    html += "</p>"

    return jsonify(result=html)


@api.route('/_load_min_omw_concept/<ss>')
@api.route('/_load_min_omw_concept_ili/<ili_id>')
def min_omw_concepts(ss=None, ili_id=None):
    if ili_id:
        ss_ids = f_ss_id_by_ili_id(ili_id)
    else:
        ss_ids = [ss]

    pos = fetch_pos()
    langs_id, langs_code = fetch_langs()
    ss, senses, defs, exes, links = fetch_ss_basic(ss_ids)
    ssrels = fetch_ssrel()

    return jsonify(result=render_template('min_omw_concept.html',
                                          pos=pos,
                                          langs=langs_id,
                                          senses=senses,
                                          ss=ss,
                                          links=links,
                                          ssrels=ssrels,
                                          defs=defs,
                                          exes=exes))


@api.route('/_load_min_omw_sense/<sID>')
def min_omw_sense(sID=None):
    langs_id, langs_code = fetch_langs()
    pos = fetch_pos()
    sense = fetch_sense(sID)
    forms = fetch_forms(sense[3])
    selected_lang = request.cookies.get('selected_lang')
    labels = fetch_labels(selected_lang, [sense[4]])
    src_meta = fetch_src_meta()
    src_sid = fetch_src_for_s_id([sID])
    #    return jsonify(result=render_template('omw_sense.html',
    return jsonify(result=render_template('min_omw_sense.html',
                                          s_id=sID,
                                          sense=sense,
                                          forms=forms,
                                          langs=langs_id,
                                          pos=pos,
                                          labels=labels,
                                          src_sid=src_sid,
                                          src_meta=src_meta))


@api.route('/_report_val2', methods=['GET', 'POST'])
@login_required(role=0, group='open')
def report_val2():
    filename = request.args.get('fn', None)
    vr, filename, wn, wn_dtls = validateFile(current_user.id, filename)

    return jsonify(result=render_template('validation-report.html',
                                          vr=vr, wn=wn, wn_dtls=wn_dtls, filename=filename))
