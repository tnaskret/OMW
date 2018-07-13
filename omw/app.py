from _md5 import md5
from functools import wraps

from flask import Flask, render_template, g, request, redirect, url_for, flash, jsonify, make_response, Markup, \
    Response, current_app

from flask_login import login_required, login_user, logout_user, current_user, UserMixin
from collections import OrderedDict as od

from itsdangerous import URLSafeTimedSerializer

from lib.safe_next_url import safe_next_url
from lib.common_sql import connect_admin, connect_omw, fetch_id_from_userid, fetch_userid, query_omw_direct, query_omw, \
    fetch_allusers

from lib.omw_sql import rate_ili_id, f_rate_summary, fetch_ssrel, fetch_labels, fetch_src_for_ss_id, fetch_src_meta, \
    fetch_core, fetch_ili, fetch_ss_basic, fetch_langs, fetch_pos, f_ss_id_by_ili_id, fetch_sense, fetch_forms, \
    fetch_src_for_s_id, f_src_id_by_proj_ver, fetch_ss_id_by_src_orginalkey, fetch_src, dd, fetch_ssrel_stats, \
    fetch_src_id_pos_stats, fetch_src_id_stats, fetch_kind, fetch_status, fetch_ili_status, fetch_proj, \
    insert_new_language, insert_new_project, updateLabels, fetch_comment_id, fetch_rate_id, comment_ili_id

from lib.wn_syntax import licenses, uploadFile, validateFile, confirmUpload

from math import log

from omw.extensions import (
    login_manager
)


def create_app(settings_override=None):
    """
    Create a Flask application using the app factory pattern.

    :param settings_override: Override settings
    :return: Flask app
    """
    app = Flask(__name__, instance_relative_config=True)

    app.config.from_object('config.settings')
    app.config.from_pyfile('settings.py', silent=True)

    if settings_override:
        app.config.update(settings_override)

    extensions(app)
    authentication(app)

    @app.route("/login", methods=["GET", "POST"])
    def login():
        """ This login function checks if the username & password
        match the admin.db; if the authentication is successful,
        it passes the id of the user into login_user() """
        if current_user.is_authenticated:
            return redirect(url_for('index'))

        if request.method == "POST" and \
                "username" in request.form and \
                "password" in request.form:
            username = request.form["username"]
            password = request.form["password"]
            user = User.get(username)

            # If we found a user based on username then compare that the submitted
            # password matches the password in the database. The password is stored
            # is a slated hash format, so you must hash the password before comparing it.
            if user and hash_pass(password) == user.password:

                if login_user(user, remember=True) and user.is_active:
                    next_url = request.form.get('next')
                    if next_url:
                        return redirect(safe_next_url(next_url))
                    return redirect(url_for("index"))
                else:
                    flash('This account has been disabled.', 'error')
            else:
                flash('Identity or password is incorrect.', 'error')
        return render_template("login.html")

    @app.route("/logout")
    @login_required(role=0, group='open')
    def logout():
        logout_user()
        return redirect(url_for("index"))

    ################################################################################

    ################################################################################
    # SET UP CONNECTION WITH DATABASES
    ################################################################################
    @app.before_request
    def before_request():
        g.admin = connect_admin()
        g.omw = connect_omw()

    @app.teardown_request
    def teardown_request(exception):
        if hasattr(g, 'db'):
            g.admin.close()
            g.omw.close()

    ################################################################################

    ################################################################################
    # AJAX REQUESTS
    ################################################################################
    @app.route('/_thumb_up_id')
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

    @app.route('/_thumb_down_id')
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

    @app.route('/_comment_id')
    def comment_id():
        user = fetch_id_from_userid(current_user.id)
        ili_id = request.args.get('ili_id', None)
        comment = request.args.get('comment', None)
        comment = str(Markup.escape(comment))
        dbinsert = comment_ili_id(ili_id, comment, user)
        return jsonify(result=dbinsert)

    @app.route('/_detailed_id')
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

    @app.route('/_confirm_wn_upload')
    def confirm_wn_upload_id():
        user = fetch_id_from_userid(current_user.id)
        fn = request.args.get('fn', None)
        upload = confirmUpload(fn, user)
        labels = updateLabels()
        return jsonify(result=upload)

    @app.route('/_add_new_project')
    def add_new_project():
        user = fetch_id_from_userid(current_user.id)
        proj = request.args.get('proj_code', None)
        proj = str(Markup.escape(proj))
        if user and proj:
            dbinsert = insert_new_project(proj, user)
            return jsonify(result=dbinsert)
        else:
            return jsonify(result=False)

    @app.route("/_load_lang_selector", methods=["GET"])
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

    @app.route('/_add_new_language')
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

    @app.route('/_load_proj_details')
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

    @app.route('/_load_min_omw_concept/<ss>')
    @app.route('/_load_min_omw_concept_ili/<ili_id>')
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

    @app.route('/_load_min_omw_sense/<sID>')
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

    @app.route('/_report_val2', methods=['GET', 'POST'])
    @login_required(role=0, group='open')
    def report_val2():

        filename = request.args.get('fn', None)
        vr, filename, wn, wn_dtls = validateFile(current_user.id, filename)

        return jsonify(result=render_template('validation-report.html',
                                              vr=vr, wn=wn, wn_dtls=wn_dtls, filename=filename))

    ################################################################################

    ################################################################################
    # VIEWS
    ################################################################################
    @app.route('/', methods=['GET', 'POST'])
    def index():
        return render_template('index.html')

    @app.route('/ili', methods=['GET', 'POST'])
    def ili_welcome(name=None):
        return render_template('ili_welcome.html')

    @app.route('/omw', methods=['GET', 'POST'])
    def omw_welcome(name=None):
        lang_id, lang_code = fetch_langs()
        src_meta = fetch_src_meta()
        ### sort by language, project version (Newest first)
        src_sort = od()
        keys = list(src_meta.keys())
        keys.sort(key=lambda x: src_meta[x]['version'], reverse=True)
        keys.sort(key=lambda x: src_meta[x]['id'])
        keys.sort(key=lambda x: lang_id[lang_code['code'][src_meta[x]['language']]][1])
        for k in keys:
            src_sort[k] = src_meta[k]
        return render_template('omw_welcome.html',
                               src_meta=src_sort,
                               lang_id=lang_id,
                               lang_code=lang_code,
                               licenses=licenses)

    @app.route('/wordnet', methods=['GET', 'POST'])
    def wordnet_license(name=None):
        return render_template('wordnet_license.html')

    @app.route('/omw_wns', methods=['GET', 'POST'])
    def omw_wns(name=None):
        src_meta = fetch_src_meta()
        stats = []
        lang_id, lang_code = fetch_langs()
        ### sort by language name (1), id, version (FIXME -- reverse version)
        for src_id in sorted(src_meta, key=lambda x: (lang_id[lang_code['code'][src_meta[x]['language']]][1],
                                                      src_meta[x]['id'],
                                                      src_meta[x]['version'])):
            stats.append((src_meta[src_id], fetch_src_id_stats(src_id)))
        return render_template('omw_wns.html',
                               stats=stats,
                               lang_id=lang_id,
                               lang_code=lang_code,
                               licenses=licenses)

    @app.route("/useradmin", methods=["GET"])
    @login_required(role=99, group='admin')
    def useradmin():
        users = fetch_allusers()
        return render_template("useradmin.html", users=users)

    @app.route("/langadmin", methods=["GET"])
    @login_required(role=99, group='admin')
    def langadmin():
        lang_id, lang_code = fetch_langs()
        return render_template("langadmin.html", langs=lang_id)

    @app.route("/projectadmin", methods=["GET"])
    @login_required(role=99, group='admin')
    def projectadmin():
        projs = fetch_proj()
        return render_template("projectadmin.html", projs=projs)

    @app.route('/allconcepts', methods=['GET', 'POST'])
    def allconcepts():
        ili, ili_defs = fetch_ili()
        rsumm, up_who, down_who = f_rate_summary(list(ili.keys()))
        return render_template('concept-list.html', ili=ili,
                               rsumm=rsumm, up_who=up_who, down_who=down_who)

    @app.route('/temporary', methods=['GET', 'POST'])
    def temporary():
        ili = fetch_ili_status(2)
        rsumm, up_who, down_who = f_rate_summary(list(ili.keys()))
        return render_template('concept-list.html', ili=ili,
                               rsumm=rsumm, up_who=up_who, down_who=down_who)

    @app.route('/deprecated', methods=['GET', 'POST'])
    def deprecated():
        ili = fetch_ili_status(0)
        rsumm, up_who, down_who = f_rate_summary(list(ili.keys()))
        return render_template('concept-list.html', ili=ili,
                               rsumm=rsumm, up_who=up_who, down_who=down_who)

    @app.route('/ili/concepts/<c>', methods=['GET', 'POST'])
    def concepts_ili(c=None):
        c = c.split(',')
        ili, ili_defs = fetch_ili(c)
        rsumm, up_who, down_who = f_rate_summary(list(ili.keys()))

        return render_template('concept-list.html', ili=ili,
                               rsumm=rsumm, up_who=up_who, down_who=down_who)

    @app.route('/ili/search', methods=['GET', 'POST'])
    @app.route('/ili/search/<q>', methods=['GET', 'POST'])
    def search_ili(q=None):

        if q:
            query = q
        else:
            query = request.form['query']

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

    @app.route('/upload', methods=['GET', 'POST'])
    @login_required(role=0, group='open')
    def upload():
        return render_template('upload.html')

    @app.route('/metadata', methods=['GET', 'POST'])
    def metadata():
        return render_template('metadata.html')

    @app.route('/join', methods=['GET', 'POST'])
    def join():
        return render_template('join.html')

    @app.route('/ili/validation-report', methods=['GET', 'POST'])
    @login_required(role=0, group='open')
    def validation_report():

        vr, filename, wn, wn_dtls = validateFile(current_user.id)

        return render_template('validation-report.html',
                               vr=vr, wn=wn, wn_dtls=wn_dtls,
                               filename=filename)

    @app.route('/ili/report', methods=['GET', 'POST'])
    @login_required(role=0, group='open')
    def report():
        passed, filename = uploadFile(current_user.id)
        return render_template('report.html',
                               passed=passed,
                               filename=filename)
        # return render_template('report.html')

    @app.route('/omw/search', methods=['GET', 'POST'])
    @app.route('/omw/search/<lang>,<lang2>/<q>', methods=['GET', 'POST'])
    def search_omw(lang=None, lang2=None, q=None):

        if lang and q:
            lang_id = lang
            lang_id2 = lang2
            query = q
        else:
            lang_id = request.form['lang']
            lang_id2 = request.form['lang2']
            query = request.form['query']
            query = query.strip()

        sense = dd(list)
        lang_sense = dd(lambda: dd(list))

        # GO FROM FORM TO SENSE
        for s in query_omw("""
            SELECT s.id as s_id, ss_id,  wid, fid, lang_id, pos_id, lemma
            FROM (SELECT w_id as wid, form.id as fid, lang_id, pos_id, lemma
                  FROM (SELECT id, lang_id, pos_id, lemma
                        FROM f WHERE lemma GLOB ? AND lang_id in (?,?)) as form
                  JOIN wf_link ON form.id = wf_link.f_id) word
            JOIN s ON wid=w_id
            """, ['[' + query[0].upper() + query[0].lower() + ']' + query[1:],
                  lang_id,
                  lang_id2]):
            sense[s['ss_id']] = [s['s_id'], s['wid'], s['fid'],
                                 s['lang_id'], s['pos_id'], s['lemma']]

            lang_sense[s['lang_id']][s['ss_id']] = [s['s_id'], s['wid'], s['fid'],
                                                    s['pos_id'], s['lemma']]

        pos = fetch_pos()
        lang_dct, lang_code = fetch_langs()
        ss, senses, defs, exes, links = fetch_ss_basic(sense.keys())

        labels = fetch_labels(lang_id, set(senses.keys()))

        resp = make_response(render_template('omw_results.html',
                                             langsel=int(lang_id),
                                             langsel2=int(lang_id2),
                                             pos=pos,
                                             lang_dct=lang_dct,
                                             sense=sense,
                                             senses=senses,
                                             ss=ss,
                                             links=links,
                                             defs=defs,
                                             exes=exes,
                                             labels=labels))

        resp.set_cookie('selected_lang', lang_id)
        resp.set_cookie('selected_lang2', lang_id2)
        return resp

    @app.route('/omw/core', methods=['GET', 'POST'])
    def omw_core():  ### FIXME add lang as a paramater?
        return render_template('omw_core.html')

    @app.route('/omw/concepts/<ssID>', methods=['GET', 'POST'])
    @app.route('/omw/concepts/ili/<iliID>', methods=['GET', 'POST'])
    def concepts_omw(ssID=None, iliID=None):

        if iliID:
            ss_ids = f_ss_id_by_ili_id(iliID)
            ili, ilidefs = fetch_ili([iliID])
        else:
            ss_ids = [ssID]
            ili, ili_defs = dict(), dict()
        pos = fetch_pos()
        langs_id, langs_code = fetch_langs()

        ss, senses, defs, exes, links = fetch_ss_basic(ss_ids)
        if (not iliID) and int(ssID) in ss:
            iliID = ss[int(ssID)][0]
            ili, ilidefs = fetch_ili([iliID])

        sss = list(ss.keys())
        for s in links:
            for l in links[s]:
                sss.extend(links[s][l])
        selected_lang = request.cookies.get('selected_lang')
        labels = fetch_labels(selected_lang, set(sss))

        ssrels = fetch_ssrel()

        ss_srcs = fetch_src_for_ss_id(ss_ids)
        src_meta = fetch_src_meta()
        core_ss, core_ili = fetch_core()
        return render_template('omw_concept.html',
                               ssID=ssID,
                               iliID=iliID,
                               pos=pos,
                               langs=langs_id,
                               senses=senses,
                               ss=ss,
                               links=links,
                               ssrels=ssrels,
                               defs=defs,
                               exes=exes,
                               ili=ili,
                               selected_lang=selected_lang,
                               selected_lang2=request.cookies.get('selected_lang2'),
                               labels=labels,
                               ss_srcs=ss_srcs,
                               src_meta=src_meta,
                               core=core_ss)

    @app.route('/omw/senses/<sID>', methods=['GET', 'POST'])
    def omw_sense(sID=None):
        langs_id, langs_code = fetch_langs()
        pos = fetch_pos()
        sense = fetch_sense(sID)
        forms = fetch_forms(sense[3])
        selected_lang = request.cookies.get('selected_lang')
        labels = fetch_labels(selected_lang, [sense[4]])
        src_meta = fetch_src_meta()
        src_sid = fetch_src_for_s_id([sID])
        return render_template('omw_sense.html',
                               s_id=sID,
                               sense=sense,
                               forms=forms,
                               langs=langs_id,
                               pos=pos,
                               labels=labels,
                               src_sid=src_sid,
                               src_meta=src_meta)

    # URIs FOR ORIGINAL CONCEPT KEYS, BY INDIVIDUAL SOURCES
    @app.route('/omw/src/<src>/<originalkey>', methods=['GET', 'POST'])
    def src_omw(src=None, originalkey=None):

        try:
            proj = src[:src.index('-')]
            ver = src[src.index('-') + 1:]
            src_id = f_src_id_by_proj_ver(proj, ver)
        except:
            src_id = None

        if src_id:
            ss = fetch_ss_id_by_src_orginalkey(src_id, originalkey)
        else:
            ss = None

        return concepts_omw(ss)

    # show wn statistics
    @app.route('/omw/src/<src>', methods=['GET', 'POST'])
    def omw_wn(src=None):
        if src:
            try:
                proj = src[:src.index('-')]
                ver = src[src.index('-') + 1:]
                src_id = f_src_id_by_proj_ver(proj, ver)
            except:
                src_id = None
            srcs_meta = fetch_src_meta()
            src_info = srcs_meta[src_id]

        return render_template('omw_wn.html',
                               wn=src,
                               src_id=src_id,
                               src_info=src_info,
                               ssrel_stats=fetch_ssrel_stats(src_id),
                               pos_stats=fetch_src_id_pos_stats(src_id),
                               src_stats=fetch_src_id_stats(src_id),
                               licenses=licenses)

    @app.route('/omw/src-latex/<src>', methods=['GET', 'POST'])
    def omw_wn_latex(src=None):
        if src:
            try:
                proj = src[:src.index('-')]
                ver = src[src.index('-') + 1:]
                src_id = f_src_id_by_proj_ver(proj, ver)
            except:
                src_id = None
            srcs_meta = fetch_src_meta()
            src_info = srcs_meta[src_id]

        return render_template('omw_wn_latex.html',
                               wn=src,
                               src_id=src_id,
                               src_info=src_info,
                               ssrel_stats=fetch_ssrel_stats(src_id),
                               pos_stats=fetch_src_id_pos_stats(src_id),
                               src_stats=fetch_src_id_stats(src_id))

    @app.route('/cili.tsv')
    def generate_cili_tsv():
        tsv = """# omw_id	ili_id	projects\n"""
        srcs = fetch_src()
        ss = dict()
        r = query_omw_direct("SELECT id, ili_id from ss")
        for (ss_id, ili_id) in r:
            ss[ss_id] = [ili_id]
        src = dd(list)
        r = query_omw_direct("SELECT ss_id, src_id, src_key from ss_src")
        for (ss_id, src_id, src_key) in r:
            src[ss_id].append("{}-{}:{}".format(srcs[src_id][0],
                                                srcs[src_id][1],
                                                src_key))

        for ss_id in ss:
            ili = 'i' + str(ss[ss_id][0]) if ss[ss_id][0] else 'None'

            tsv += "{}\t{}\t{}\n".format(ss_id, ili, ";".join(src[ss_id]))
        return Response(tsv, mimetype='text/tab-separated-values')

    @app.context_processor
    def utility_processor():
        def scale_freq(f, maxfreq=1000):
            if f > 0:
                return 100 + 100 * log(f) / log(maxfreq)
            else:
                return 100

        return dict(scale_freq=scale_freq)

    def hash_pass(password):
        """ Return the md5 hash of the password+salt """
        salted_password = password + app.secret_key
        return md5(salted_password.encode('utf-8')).hexdigest()

    return app


def login_required(role=0, group='open'):
        """
        This is a redefinition of the decorator login_required,
        to include a 'role' argument to allow users with different
        roles access different views and a group access to close some
        views by groups. For example:
        @login_required(role=0, group='ntuwn')   0 = for all
        """

        def wrapper(fn):
            @wraps(fn)
            def decorated_view(*args, **kwargs):
                if not current_user.is_authenticated:
                    return login_manager.unauthorized()
                if current_user.role < role:
                    return login_manager.unauthorized()
                if group != 'open' and current_user.group != group:
                    return login_manager.unauthorized()

                return fn(*args, **kwargs)

            return decorated_view

        return wrapper


def extensions(app):
    """
    Register 0 or more extensions (mutates the app passed in).

    :param app: Flask application instance
    :return: None
    """
    login_manager.init_app(app)

    return None


def authentication(app):
    """
    Initialize the Flask-Login extension (mutates the app passed in).

    :param app: Flask application instance
    :param user_model: Model that contains the authentication information
    :type user_model: SQLAlchemy model
    :return: None
    """
    login_manager.login_view = '/login'
    login_manager.login_message = "You don't seem to have permission to see this content."

    @login_manager.user_loader
    def load_user(userID):
        """ This function, given an user_id, needs to check whether this user
        'is active' / 'exists' [FIXME, this should be done against the DB?],
        and returns an User object. I DONT THINK SO ANYMORE!"""

        """
        Flask-Login user_loader callback.
        The user_loader function asks this function to get a User Object or return
        None based on the userid.
        The userid was stored in the session environment by Flask-Login.
        user_loader stores the returned User object in current_user during every
        flask request.
        """
        return User.get(userID)


class User(UserMixin):
    def __init__(self, userID, password, role, group):
        self.id = userID
        self.password = password
        self.role = role
        self.group = group

    def get_auth_token(self):
        """ Encode a secure token for cookie """
        data = [str(self.id), self.password]
        login_serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        return login_serializer.dumps(data)

    def get_role(self):
        """ Returns the role (access level) for the user """
        return self.role

    @staticmethod
    def get(userid):
        """
        Static method to search the database and see if userid exists.
        If it does exist then return a User Object. If not then return
        None, as required by Flask-Login.
        """
        user = fetch_userid(userid)

        if user:
            return User(user[0], user[1], user[2], user[3])
        else:
            return None
