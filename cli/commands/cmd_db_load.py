import click

import sqlite3
import os
import nltk

from iso639 import languages
from omw.app import create_app, sys, dd
from nltk.corpus import wordnet as wn

# Create an app context for the database connection.
app = create_app()

omw_db = os.path.realpath(
    os.path.join(os.getcwd(), 'db', app.config['OMW_DATABASE_FILE_NAME']))

admin_db = os.path.realpath(
    os.path.join(os.getcwd(), 'db', app.config['ADMIN_DATABASE_FILE_NAME']))


@click.group()
def cli():
    """ Run SqlLite related tasks to populate database"""
    pass


@click.command()
def ili_kinds():
    """
    Loads ili kinds data.

    :return: None
    """
    if os.path.isfile(omw_db):
        omw_connection = sqlite3.connect(omw_db)
        cursor = omw_connection.cursor()

        u = "load ili_kinds"

        cursor.execute("""INSERT INTO kind (id, kind, u) 
                   VALUES (?,?,?)""", [1, 'concept', u])

        cursor.execute("""INSERT INTO kind (id, kind, u) 
                   VALUES (?,?,?)""", [2, 'instance', u])
        omw_connection.commit()
        omw_connection.close()
        sys.stdout.write('Loading ili kinds finished\n')
    else:
        sys.stdout.write('Unable to find database (%s) file\n' % omw_db)
    return None


@click.command()
def ili_status():
    """
    Loads ili statuses.

    :return: None
    """
    if os.path.isfile(omw_db):
        omw_connection = sqlite3.connect(omw_db)
        cursor = omw_connection.cursor()

        u = "load ili_status"

        cursor.execute("""INSERT INTO status (id, status, u) 
               VALUES (?,?,?)""", [0, 'deprecated', u])

        cursor.execute("""INSERT INTO status (id, status, u) 
               VALUES (?,?,?)""", [1, 'normal', u])

        cursor.execute("""INSERT INTO status (id, status, u) 
               VALUES (?,?,?)""", [2, 'temporary', u])

        omw_connection.commit()
        omw_connection.close()
        sys.stdout.write('Loading ili statuses finished\n')
    else:
        sys.stdout.write('Unable to find database (%s) file\n' % omw_db)
    return None


@click.command()
def part_of_speech():
    """
    Loads parts of speech.

    :return: None
    """
    if os.path.isfile(omw_db):
        omw_connection = sqlite3.connect(omw_db)
        cursor = omw_connection.cursor()

        u = "load pos"

        cursor.execute("""INSERT INTO pos (tag, def, u) 
               VALUES (?,?,?)""", ['n', 'noun', u])

        cursor.execute("""INSERT INTO pos (tag, def, u) 
               VALUES (?,?,?)""", ['v', 'verb', u])

        cursor.execute("""INSERT INTO pos (tag, def, u) 
               VALUES (?,?,?)""", ['a', 'adjective', u])

        cursor.execute("""INSERT INTO pos (tag, def, u) 
               VALUES (?,?,?)""", ['r', 'adverb', u])

        cursor.execute("""INSERT INTO pos (tag, def, u) 
               VALUES (?,?,?)""", ['s', 'adverb satellite', u])

        cursor.execute("""INSERT INTO pos (tag, def, u) 
               VALUES (?,?,?)""", ['c', 'conjunction', u])

        cursor.execute("""INSERT INTO pos (tag, def, u)
               VALUES (?,?,?)""", ['p', 'adposition', u])

        cursor.execute("""INSERT INTO pos (tag, def, u) 
               VALUES (?,?,?)""", ['x', 'other (incl. particles, classifiers, bound morphemes, determiners, etc.)', u])

        cursor.execute("""INSERT INTO pos (tag, def, u) 
               VALUES (?,?,?)""", ['z', 'multiword expression (inc. phrases, idioms, etc.)', u])

        cursor.execute("""INSERT INTO pos (tag, def, u) 
               VALUES (?,?,?)""", ['u', 'unknown', u])

        omw_connection.commit()
        omw_connection.close()
        sys.stdout.write('Loading parts of speech finished\n')
    else:
        sys.stdout.write('Unable to find database (%s) file\n' % omw_db)
    return None


@click.command()
def sense_relation_types():
    """
    Loads sense relation types.

    :return: None
    """
    if os.path.isfile(omw_db):

        u = "load srel types"

        srel_file = os.path.realpath(
            os.path.join(os.getcwd(), 'sql_scripts', 'srel.tab'))

        if os.path.isfile(srel_file):

            omw_connection = sqlite3.connect(omw_db)
            cursor = omw_connection.cursor()

            f = open(srel_file, 'r')
            for line in f:
                cursor.execute("""INSERT INTO srel (rel, def, u) 
                     VALUES (?,?,?)""", line.strip().split('\t') + [u])
            f.close()
            omw_connection.commit()
            omw_connection.close()
            sys.stdout.write('Loading sense relations finished\n')

        else:
            sys.stdout.write("Can't open file (%s)\n" % srel_file)
    else:
        sys.stdout.write('Unable to find database (%s) file\n' % omw_db)
    return None


@click.command()
def synset_relation_types():
    """
    Loads synset relation types.

    :return: None
    """
    if os.path.isfile(omw_db):

        u = "load ssrel types"

        ssrel_file = os.path.realpath(
            os.path.join(os.getcwd(), 'sql_scripts', 'ssrel.tab'))

        if os.path.isfile(ssrel_file):

            omw_connection = sqlite3.connect(omw_db)
            cursor = omw_connection.cursor()

            f = open(ssrel_file, 'r')
            for line in f:
                cursor.execute("""INSERT INTO ssrel (rel, def, u)
                             VALUES (?,?,?)""", line.strip().split('\t') + [u])
            f.close()
            omw_connection.commit()
            omw_connection.close()
            sys.stdout.write('Loading synset relations finished\n')

        else:
            sys.stdout.write("Can't open file (%s)\n" % ssrel_file)
    else:
        sys.stdout.write('Unable to find database (%s) file\n' % omw_db)
    return None


# TODO this will require more refactoring
@click.command()
def pwn():
    """
    Loads nltk wordnet and populates database.

    :return: None
    """
    nltk.download('wordnet')

    u = "load pwn"

    if os.path.isfile(omw_db):
        omw_connection = sqlite3.connect(omw_db)
        cursor = omw_connection.cursor()

        vframe = dd(lambda: dd(str))
        vframe['eng'][1] = "Something ----s"
        vframe['eng'][2] = "Somebody ----s"
        vframe['eng'][3] = "It is ----ing"
        vframe['eng'][4] = "Something is ----ing PP"
        vframe['eng'][5] = "Something ----s something Adjective/Noun"
        vframe['eng'][6] = "Something ----s Adjective/Noun"
        vframe['eng'][7] = "Somebody ----s Adjective"
        vframe['eng'][8] = "Somebody ----s something"
        vframe['eng'][9] = "Somebody ----s somebody"
        vframe['eng'][10] = "Something ----s somebody"
        vframe['eng'][11] = "Something ----s something"
        vframe['eng'][12] = "Something ----s to somebody"
        vframe['eng'][13] = "Somebody ----s on something"
        vframe['eng'][14] = "Somebody ----s somebody something"
        vframe['eng'][15] = "Somebody ----s something to somebody"
        vframe['eng'][16] = "Somebody ----s something from somebody"
        vframe['eng'][17] = "Somebody ----s somebody with something"
        vframe['eng'][18] = "Somebody ----s somebody of something"
        vframe['eng'][19] = "Somebody ----s something on somebody"
        vframe['eng'][20] = "Somebody ----s somebody PP"
        vframe['eng'][21] = "Somebody ----s something PP"
        vframe['eng'][22] = "Somebody ----s PP"
        vframe['eng'][23] = "Somebody's (body part) ----s"
        vframe['eng'][24] = "Somebody ----s somebody to INFINITIVE"
        vframe['eng'][25] = "Somebody ----s somebody INFINITIVE"
        vframe['eng'][26] = "Somebody ----s that CLAUSE"
        vframe['eng'][27] = "Somebody ----s to somebody"
        vframe['eng'][28] = "Somebody ----s to INFINITIVE"
        vframe['eng'][29] = "Somebody ----s whether INFINITIVE"
        vframe['eng'][30] = "Somebody ----s somebody into V-ing something"
        vframe['eng'][31] = "Somebody ----s something with something"
        vframe['eng'][32] = "Somebody ----s INFINITIVE"
        vframe['eng'][33] = "Somebody ----s VERB-ing"
        vframe['eng'][34] = "It ----s that CLAUSE"
        vframe['eng'][35] = "Something ----s INFINITIVE "

        # Verb Frames Symbols per Verb_id
        vframe['engsym'][1] = "☖ ~"
        vframe['engsym'][2] = "☺ ~"
        vframe['engsym'][3] = "It is ~ing"
        vframe['engsym'][4] = "☖ is ~ing PP"
        vframe['engsym'][5] = "☖ ~ ☖ Adj/N"
        vframe['engsym'][6] = "☖ ~ Adj/N"
        vframe['engsym'][7] = "☺ ~ Adj"
        vframe['engsym'][8] = "☺ ~ ☖"
        vframe['engsym'][9] = "☺ ~ ☺"
        vframe['engsym'][10] = "☖ ~ ☺"
        vframe['engsym'][11] = "☖ ~ ☖"
        vframe['engsym'][12] = "☖ ~ to ☺"
        vframe['engsym'][13] = "☺ ~ on ☖"
        vframe['engsym'][14] = "☺ ~ ☺ ☖"
        vframe['engsym'][15] = "☺ ~ ☖ to ☺"
        vframe['engsym'][16] = "☺ ~ ☖ from ☺"
        vframe['engsym'][17] = "☺ ~ ☺ with ☖"
        vframe['engsym'][18] = "☺ ~ ☺ of ☖"
        vframe['engsym'][19] = "☺ ~ ☖ on ☺"
        vframe['engsym'][20] = "☺ ~ ☺ PP"
        vframe['engsym'][21] = "☺ ~ ☖ PP"
        vframe['engsym'][22] = "☺ ~ PP"
        vframe['engsym'][23] = "☺'s (body part) ~"
        vframe['engsym'][24] = "☺ ~ ☺ to INF"
        vframe['engsym'][25] = "☺ ~ ☺ INF"
        vframe['engsym'][26] = "☺ ~ that CLAUSE"
        vframe['engsym'][27] = "☺ ~ to ☺"
        vframe['engsym'][28] = "☺ ~ to INF"
        vframe['engsym'][29] = "☺ ~ whether INF"
        vframe['engsym'][30] = "☺ ~ ☺ into  Ving ☖"
        vframe['engsym'][31] = "☺ ~ ☖ with ☖"
        vframe['engsym'][32] = "☺ ~ INF"
        vframe['engsym'][33] = "☺ ~ V-ing"
        vframe['engsym'][34] = "It ~ that CLAUSE"
        vframe['engsym'][35] = "☖ ~ INF "

        lexnames = """0	adj.all	all adjective clusters
        1	adj.pert	relational adjectives (pertainyms)
        2	adv.all	all adverbs
        3	noun.Tops	unique beginner for nouns
        4	noun.act	nouns denoting acts or actions
        5	noun.animal	nouns denoting animals
        6	noun.artifact	nouns denoting man-made objects
        7	noun.attribute	nouns denoting attributes of people and objects
        8	noun.body	nouns denoting body parts
        9	noun.cognition	nouns denoting cognitive processes and contents
        10	noun.communication	nouns denoting communicative processes and contents
        11	noun.event	nouns denoting natural events
        12	noun.feeling	nouns denoting feelings and emotions
        13	noun.food	nouns denoting foods and drinks
        14	noun.group	nouns denoting groupings of people or objects
        15	noun.location	nouns denoting spatial position
        16	noun.motive	nouns denoting goals
        17	noun.object	nouns denoting natural objects (not man-made)
        18	noun.person	nouns denoting people
        19	noun.phenomenon	nouns denoting natural phenomena
        20	noun.plant	nouns denoting plants
        21	noun.possession	nouns denoting possession and transfer of possession
        22	noun.process	nouns denoting natural processes
        23	noun.quantity	nouns denoting quantities and units of measure
        24	noun.relation	nouns denoting relations between people or things or ideas
        25	noun.shape	nouns denoting two and three dimensional shapes
        26	noun.state	nouns denoting stable states of affairs
        27	noun.substance	nouns denoting substances
        28	noun.time	nouns denoting time and temporal relations
        29	verb.body	verbs of grooming, dressing and bodily care
        30	verb.change	verbs of size, temperature change, intensifying, etc.
        31	verb.cognition	verbs of thinking, judging, analyzing, doubting
        32	verb.communication	verbs of telling, asking, ordering, singing
        33	verb.competition	verbs of fighting, athletic activities
        34	verb.consumption	verbs of eating and drinking
        35	verb.contact	verbs of touching, hitting, tying, digging
        36	verb.creation	verbs of sewing, baking, painting, performing
        37	verb.emotion	verbs of feeling
        38	verb.motion	verbs of walking, flying, swimming
        39	verb.perception	verbs of seeing, hearing, feeling
        40	verb.possession	verbs of buying, selling, owning
        41	verb.social	verbs of political and social activities and events
        42	verb.stative	verbs of being, having, spatial relations
        43	verb.weather	verbs of raining, snowing, thawing, thundering
        44	adj.ppl	participial adjectives"""

        # Short and Full Lexnames per Lexid
        lexname = dd(lambda: dd(str))
        for line in lexnames.split('\n'):
            lexnlst = line.split('\t')
            lexname['eng'][lexnlst[1]] = lexnlst[2]
            lexname['id'][lexnlst[1]] = lexnlst[0]

        ################################################################
        # GET PWN3.0-ILI ORIGINAL MAPPING
        ################################################################

        ili_map_file = os.path.realpath(
            os.path.join(os.getcwd(), 'sql_scripts', 'ili-map.tab'))

        f = open(ili_map_file, 'r')
        ili_map = dict()
        for line in f:
            if line.strip() == "":
                continue
            else:
                tab = line.split('\t')
                pwn_ss = tab[1].strip()
                ili_id = tab[0][1:].strip()
                ili_map[pwn_ss] = ili_id

        ################################################################
        # INSERT PROJECT / SRC / SRC_META DATA
        ################################################################

        cursor.execute("""INSERT INTO proj (code, u)
                     VALUES (?,?)""", ['pwn', u])

        cursor.execute("""SELECT MAX(id) FROM proj""")
        proj_id = cursor.fetchone()[0]

        sys.stderr.write('PWN was attributed ({}) as proj_id.\n'.format(proj_id))

        cursor.execute("""INSERT INTO src (proj_id, version, u)
                     VALUES (?,?,?)""", [proj_id, '3.0', u])

        cursor.execute("""SELECT MAX(id) FROM src""")
        src_id = cursor.fetchone()[0]

        sys.stdout.write('PWN30 was attributed (%s) as src_id.\n' % (src_id))

        cursor.execute("""INSERT INTO src_meta (src_id, attr, val, u)
                     VALUES (?,?,?,?)""", [src_id, 'id', 'pwn', u])

        cursor.execute("""INSERT INTO src_meta (src_id, attr, val, u)
                     VALUES (?,?,?,?)""", [src_id, 'version', '3.0', u])

        cursor.execute("""INSERT INTO src_meta (src_id, attr, val, u)
                     VALUES (?,?,?,?)""", [src_id, 'label', 'Princeton Wordnet 3.0', u])

        cursor.execute("""INSERT INTO src_meta (src_id, attr, val, u)
                     VALUES (?,?,?,?)""", [src_id, 'license', 'https://wordnet.princeton.edu/wordnet/license/', u])

        cursor.execute("""INSERT INTO src_meta (src_id, attr, val, u)
                     VALUES (?,?,?,?)""", [src_id, 'language', 'en', u])

        sys.stdout.write('PWN30 meta-data was added.\n')

        ################################################################
        # INSERT (WN-EXTERNAL) RESOURCE DATA
        ################################################################

        # FIXME!!! ADD SRC_META

        cursor.execute("""INSERT INTO resource (code, u)
                   VALUES (?,?)""", ['pwn30-lexnames', u])

        cursor.execute("""SELECT MAX(id) FROM resource""")
        lexnames_resource_id = cursor.fetchone()[0]

        cursor.execute("""INSERT INTO resource (code, u)
                   VALUES (?,?)""", ['pwn30-verbframes', u])

        cursor.execute("""SELECT MAX(id) FROM resource""")
        verbframes_resource_id = cursor.fetchone()[0]

        ################################################################
        # INSERT LANG DATA (CODES AND NAMES)
        ################################################################

        cursor.execute("""INSERT INTO lang (bcp47, iso639, u)
                     VALUES (?,?,?)""", ['en', 'eng', u])

        cursor.execute("""INSERT INTO lang_name (lang_id, in_lang_id, name, u)
                     VALUES (1,1,'English',?)""", [u])

        cursor.execute("""SELECT MAX(id) FROM lang""")
        lang_id = cursor.fetchone()[0]

        ################################################################
        # LOAD POS, SSREL, AND SREL DATA
        ################################################################

        pos_id = dict()
        cursor.execute("""SELECT id, tag FROM pos""")
        rows = cursor.fetchall()
        for r in rows:
            pos_id[r[1]] = r[0]

        ssrel_id = dict()
        cursor.execute("""SELECT id, rel FROM ssrel""")
        rows = cursor.fetchall()
        for r in rows:
            ssrel_id[r[1]] = r[0]

        srel_id = dict()
        cursor.execute("""SELECT id, rel FROM srel""")
        rows = cursor.fetchall()
        for r in rows:
            srel_id[r[1]] = r[0]

        ################################################################
        # ADD ENGLISH ENTRIES
        ################################################################

        ssid = dict()
        fid = dict()

        ss_lemma_sense_id = dict()

        def ss2of(ss):
            # FIXME!!!! 's' is getting through as the src_key on purpose!
            return "%08d-%s" % (ss.offset(), ss.pos())

        for ss in wn.all_synsets():

            ili_id = int(ili_map[ss2of(ss)])

            # (1) LOAD PWN CONCEPTS AS ILI CONCEPTS
            if ss.instance_hypernyms():
                kind = 2

                cursor.execute("""INSERT INTO ili (id, kind_id, def, status_id,
                                              origin_src_id, src_key, u)
                             VALUES (?,?,?,?,?,?,?)
                          """, (ili_id, kind, ss.definition(), 1,
                                src_id, ss2of(ss), u))

            else:
                kind = 1

                cursor.execute("""INSERT INTO ili (id, kind_id, def, status_id,
                                              origin_src_id, src_key, u)
                             VALUES (?,?,?,?,?,?,?)
                          """, (ili_id, kind, ss.definition(), 1,
                                src_id, ss2of(ss), u))

            # (2) LOAD PWN CONCEPTS AS OMW CONCEPTS

            pos = ss.pos()
            pid = pos_id[pos.replace('s', 'a')]

            # SYNSETS
            cursor.execute("""INSERT INTO ss (ili_id, pos_id, u)
                         VALUES (?,?,?)
                      """, (ili_id, pid, u))
            ss_id = cursor.lastrowid

            cursor.execute("""INSERT INTO ss_src (ss_id, src_id, src_key, conf, u)
                         VALUES (?,?,?,?,?)
                      """, (ss_id, src_id, ss2of(ss), 1, u))

            ssid[ss2of(ss)] = ss_id

            cursor.execute("""INSERT INTO def (ss_id, lang_id, def, u)
                         VALUES (?,?,?,?)
                      """, (ss_id, lang_id, ss.definition(), u))
            def_id = cursor.lastrowid

            cursor.execute("""INSERT INTO def_src (def_id, src_id, conf, u)
                         VALUES (?,?,?,?)
                      """, (def_id, src_id, 1, u))

            # EXAMPLES
            exs = ss.examples()

            for e in exs:
                cursor.execute("""INSERT INTO ssexe (ss_id, lang_id, ssexe, u)
                            VALUES (?,?,?,?)
                          """, (ss_id, lang_id, e, u))
                ex_id = cursor.lastrowid

                cursor.execute("""INSERT INTO ssexe_src (ssexe_id, src_id, conf, u)
                             VALUES (?,?,?,?)
                          """, (ex_id, src_id, 1, u))

            # INSERT FORMS, WORDS (SAME) and SENSES
            for l in ss.lemmas():

                # FORMS
                form = l.name().replace('_', ' ')
                if (pid, form) in fid:
                    form_id = fid[(pid, form)]
                else:
                    cursor.execute("""INSERT INTO f (lang_id, pos_id, lemma, u)
                                 VALUES (?,?,?,?)
                              """, (lang_id, pid, form, u))
                    form_id = cursor.lastrowid
                    fid[(pid, form)] = form_id

                    cursor.execute("""INSERT INTO f_src (f_id, src_id, conf, u)
                                 VALUES (?,?,?,?)
                              """, (form_id, src_id, 1, u))

                # WORDS
                cursor.execute("""INSERT INTO w (canon, u)
                             VALUES (?,?) """, (form_id, u))
                word_id = cursor.lastrowid

                cursor.execute("""INSERT INTO wf_link (w_id, f_id, src_id, conf, u)
                             VALUES (?,?,?,?,?)
                          """, (word_id, form_id, src_id, 1, u))

                # SENSES
                cursor.execute("""INSERT INTO s (ss_id, w_id, u)
                             VALUES (?,?,?) """, (ss_id, word_id, u))
                s_id = cursor.lastrowid

                cursor.execute("""INSERT INTO s_src (s_id, src_id, conf, u)
                             VALUES (?,?,?,?) """, (s_id, src_id, 1, u))

                ss_lemma_sense_id[(ss, l)] = s_id

        ################################################################
        # SECOND ROUND: INSERT RELATIONS
        ################################################################

        # This now includes all relations as named in NLTK3.0
        nltk_synlink_names = """also	also_sees
        attribute	attributes
        causes	causes
        entails	entailments
        hypernym	hypernyms
        hyponym	hyponyms
        instance_hypernym	instance_hypernyms
        instance_hyponym	instance_hyponyms
        holo_part	part_holonyms
        mero_part	part_meronyms
        similar	similar_tos
        holo_substance	substance_holonyms
        mero_substance	substance_meronyms
        holo_member	member_holonyms
        mero_member	member_meronyms
        domain_topic	topic_domains
        domain_region	region_domains
        exemplifies	usage_domains"""

        synlinks = dict()

        for line in nltk_synlink_names.splitlines():
            (k, v) = line.split('\t')
            synlinks[k.strip()] = v.strip()

        # list with relations not present in NLTK3.0
        # but that can be inserted by finding their reverse
        linkrev = dict()
        linkrev['domain_topic'] = 'has_domain_topic'
        linkrev['exemplifies'] = 'is_exemplified_by'
        linkrev['domain_region'] = 'has_domain_region'

        nltk_senslink_names = """antonym	antonyms
        pertainym	pertainyms
        derivation	derivationally_related_forms"""

        senslinks = dict()

        for line in nltk_senslink_names.splitlines():
            (k, v) = line.split('\t')
            senslinks[k.strip()] = v.strip()

        for ss in wn.all_synsets():

            pos = ss.pos()
            pid = pos_id[pos.replace('s', 'a')]

            # SSREL
            for r in synlinks.keys():
                for ss2 in getattr(ss, synlinks[r])():
                    cursor.execute("""INSERT INTO sslink (ss1_id, ssrel_id, ss2_id, u)
                                 VALUES (?,?,?,?)""",
                                   (ssid[ss2of(ss)], ssrel_id[r], ssid[ss2of(ss2)], u))
                    sslink_id = cursor.lastrowid

                    cursor.execute("""INSERT INTO sslink_src (sslink_id, src_id, conf, lang_id, u)
                                 VALUES (?,?,?,?,?)""",
                                   (sslink_id, src_id, 1, lang_id, u))

                    if r in linkrev.keys():  # insert the reverse relation

                        cursor.execute("""INSERT INTO sslink (ss1_id, ssrel_id, ss2_id, u)
                                     VALUES (?,?,?,?)""",
                                       (ssid[ss2of(ss2)], ssrel_id[linkrev[r]], ssid[ss2of(ss)], u))
                        sslink_id = cursor.lastrowid

                        cursor.execute("""INSERT INTO sslink_src (sslink_id, src_id, conf, lang_id, u)
                                     VALUES (?,?,?,?,?)""",
                                       (sslink_id, src_id, 1, lang_id, u))

            # SS LEXNAMES
            lxn = ss.lexname()

            cursor.execute("""INSERT INTO ssxl (ss_id, resource_id, x1, x2, x3, u)
                         VALUES (?,?,?,?,?,?)
                      """, (ssid[ss2of(ss)], lexnames_resource_id, lexname['id'][lxn],
                            lxn, lexname['eng'][lxn], u))

            # SS VERBFRAMES
            sframes = ss.frame_ids()
            for frame in sframes:
                cursor.execute("""INSERT INTO ssxl (ss_id, resource_id, x1, x2, x3, u)
                             VALUES (?,?,?,?,?,?)
                          """, (ssid[ss2of(ss)], verbframes_resource_id, frame,
                                vframe['eng'][frame], vframe['engsym'][frame], u))

            # SENSE LINKS
            for l1 in ss.lemmas():
                s1_id = ss_lemma_sense_id[(ss, l1)]

                lframeids = l1.frame_ids()  # lemma frames

                for frame in lframeids:
                    cursor.execute("""INSERT INTO sxl (s_id, resource_id, x1, x2, x3, u)
                                 VALUES (?,?,?,?,?,?)
                              """, (s1_id, verbframes_resource_id, frame,
                                    vframe['eng'][frame], vframe['engsym'][frame], u))

                for r in senslinks:
                    for l2 in getattr(l1, senslinks[r])():
                        s2_id = ss_lemma_sense_id[(l2.synset(), l2)]

                        cursor.execute("""INSERT INTO slink (s1_id, srel_id, s2_id, u)
                                     VALUES (?,?,?,?)""",
                                       (s1_id, srel_id[r], s2_id, u))
                        slink_id = cursor.lastrowid

                        cursor.execute("""INSERT INTO slink_src (slink_id, src_id, conf, u)
                                     VALUES (?,?,?,?)""",
                                       (slink_id, src_id, 1, u))
        omw_connection.commit()
        omw_connection.close()
        sys.stdout.write('Loading pwn finished\n')
    else:
        sys.stdout.write('Unable to find database (%s) file\n' % omw_db)

    return None


@click.command()
def core():
    """
    Reads the core data and maps it to ili
    after loads it into the xlink table.

    :return: None
    """
    if os.path.isfile(omw_db):
        omw_connection = sqlite3.connect(omw_db)
        cursor = omw_connection.cursor()

        uname = "load core"

        wn30_core_file = os.path.realpath(
            os.path.join(os.getcwd(), 'sql_scripts', 'wn30-core-synsets.tab'))

        f = open(wn30_core_file, 'r')
        core = set()
        icore = set()
        for line in f:
            if line.strip() == "":
                continue
            else:
                core.add(line.strip())

        ################################################################
        # GET PWN3.0-ILI ORIGINAL MAPPING
        ################################################################
        ili_map_file = os.path.realpath(
            os.path.join(os.getcwd(), 'sql_scripts', 'ili-map.tab'))
        f = open(ili_map_file, 'r')
        ili_map = dict()
        ili2ss = dict()
        for line in f:
            if line.strip() == "":
                continue
            else:
                tab = line.split('\t')
                pwn_ss = tab[1].strip()
                ili_id = tab[0][1:].strip()
                # ili_map[pwn_ss.replace('-s', '-a')] = ili_id
                ili2ss[int(ili_id)] = pwn_ss.replace('-s', '-a')
                # print(ili_id, pwn_ss.replace('-s', '-a'),  pwn_ss.replace('-s', '-a') in core)

        ################################################################
        # Enter core data
        ################################################################
        rname = 'core'
        values = list()

        cursor.execute('select id, ili_id from ss')
        for (ss_id, ili_id) in cursor:
            # print(ss_id, ili_id)
            if ili_id in ili2ss and ili2ss[ili_id] in core:
                values.append((ss_id, ili_id, ili2ss[ili_id]))
                # print(ss_id, ili_id, ili2ss[ili_id])

        cursor.execute('select id from resource where code = ?', (rname,))
        r = cursor.fetchone()
        if r:
            ### core already exists
            rid = r[0]
        else:
            ### enter the resource
            cursor.execute("""INSERT INTO resource(code, u) VALUES (?,?)""",
                           (rname, uname))
            rid = cursor.lastrowid
            ### enter the resource meta-data
            cursor.executemany("""INSERT INTO resource_meta (resource_id, attr, val, u) 
            VALUES (?,?,?,?)""",
                               [(rid, 'Name', "Core Synsets", uname),
                                (rid, 'Info', "x1 = 'iliid', x2='pwn-3.0 key'", uname)])

            ### enter the data
            cursor.executemany("""INSERT INTO ssxl (ss_id, resource_id,  x1, x2, u) 
            VALUES (?, ?, ?,?, ?)""", [(v[0], rid, v[1], v[2], uname) for v in values])

        omw_connection.commit()
        omw_connection.close()
        sys.stdout.write('Loading core finished\n')
    else:
        sys.stdout.write('Unable to find database (%s) file\n' % omw_db)

    return None


@click.command()
def pwn_freq():
    """
    Loads pwn frequency.

    :return: None
    """
    if os.path.isfile(omw_db):

        omw_connection = sqlite3.connect(omw_db)
        cursor = omw_connection.cursor()

        freq = dd(lambda: dd(int))

        for ss in wn.all_synsets():
            of = "{:08d}-{}".format(ss.offset(), ss.pos())
            for l in ss.lemmas():
                if int(l.count()):
                    freq[of][l.name().replace('_', ' ')] = int(l.count())  ### don't enter count=0

        sid2pwn = dict()
        pwn2sid = dict()
        cursor.execute("""SELECT ss.id, src_key 
        FROM ss JOIN ili ON ili.id = ili_id 
        WHERE origin_src_id=1""")

        for r in cursor:
            sid2pwn[r[0]] = r[1]
            pwn2sid[r[1]] = r[0]

        sense = dd(lambda: dd(int))

        cursor.execute("""
        SELECT s_id, ss_id, lemma
          FROM (SELECT w_id, canon, ss_id, s_id 
            FROM (SELECT id as s_id, ss_id, w_id FROM s) 
                 JOIN w ON w_id = w.id ) 
           JOIN f ON canon = f.id WHERE lang_id=1
        """)
        for (s_id, ss_id, lemma) in cursor:
            sense[sid2pwn[ss_id]][lemma] = s_id

        ## sense external link
        ## s_id, resource_id, x1=freq, x2=count
        values = []
        for of in freq:
            for lemma in freq[of]:
                # print (of, lemma, freq[of][lemma], sense[of][lemma])
                values.append((sense[of][lemma], 3,
                               'freq', 1, freq[of][lemma],
                               3))
        rname = 'pwn30-freq'
        cursor.executemany("""INSERT INTO sxl (s_id, resource_id,  x1, x2, x3, u) 
        VALUES (?,?, ?,?,?, ?)""", values)

        omw_connection.commit()
        omw_connection.close()
        sys.stdout.write('Loading pwn freq finished\n')
    else:
        sys.stdout.write('Unable to find database (%s) file\n' % omw_db)

    return None


@click.command()
def language():
    """
    Loads languages.

    :return: None
    """
    if os.path.isfile(omw_db):

        omw_connection = sqlite3.connect(omw_db)
        cursor = omw_connection.cursor()

        known = dict()

        cursor.execute("""SELECT id, iso639 from lang""")
        for (lid, l3) in cursor:
            known[l3] = lid

        for l3 in "eng cmn".split():
            # for l3 in "eng als arb bul cmn dan ell fas fin fra heb hrv ita jpn cat eus glg spa ind zsm nno nob pol por slv swe tha aar afr aka amh asm aze bam bel ben bod bos bre ces cor cym deu dzo epo est ewe fao ful gla gle glv guj hau hin hun hye ibo iii ina isl kal kan kat kaz khm kik kin kir kor lao lav lin lit lub lug mal mar mkd mlg mlt mon mya nbl nde nep nld oci ori orm pan pus roh ron run rus sag sin slk sme sna som sot srp ssw swa tam tel tgk tir ton tsn tso tur ukr urd uzb ven vie xho yor zul ang arz ast chr fry fur grc hat hbs ido kur lat ltg ltz mri nan nav rup san scn srd tat tgl tuk vol yid yue".split():
            if l3 in known:  ### already in
                continue

            l = languages.get(part3=l3)

            if l.part1:  ### use the two letter code if it exists
                bcp47 = l.part1
            else:
                bcp47 = l3

            # INSERT LANG DATA (CODES AND NAMES)
            u = 'omw'
            cursor.execute("""INSERT INTO lang (bcp47, iso639, u)
                          VALUES (?,?,?)""", (bcp47, l3, u))

            cursor.execute("""SELECT MAX(id) FROM lang""")
            lang_id = cursor.fetchone()[0]

            cursor.execute("""INSERT INTO lang_name (lang_id, in_lang_id, name, u)
            VALUES (?,?,?,?)""", (lang_id, known['eng'], l.name, u))

        omw_connection.commit()
        omw_connection.close()
        sys.stdout.write('Loading languages finished\n')
    else:
        sys.stdout.write('Unable to find database (%s) file\n' % omw_db)
    return None


@click.command()
@click.pass_context
def load_all(ctx):
    """
    Loads all.

    :ctx: Context
    :return: None
    """
    ctx.invoke(ili_kinds)
    ctx.invoke(ili_status)
    ctx.invoke(part_of_speech)
    ctx.invoke(synset_relation_types)
    ctx.invoke(sense_relation_types)
    ctx.invoke(pwn)
    ctx.invoke(pwn_freq)
    ctx.invoke(language)
    ctx.invoke(core)
    return None


cli.add_command(ili_kinds)
cli.add_command(ili_status)
cli.add_command(part_of_speech)
cli.add_command(sense_relation_types)
cli.add_command(synset_relation_types)
cli.add_command(pwn)
cli.add_command(pwn_freq)
cli.add_command(core)
cli.add_command(language)
cli.add_command(load_all)
