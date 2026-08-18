/* _1653_proto_map_data.h — GENERATED, do not hand-edit.
 *
 * Produced by docs/srmech/notes/_1653_map_emit_data_rc444.py from:
 *   docs/srmech/python/srmech/cascade/catalogs/cascade_catalog/klein4_from_one.toml
 *   sha256 85d3dbcf21bd2d8d4b8ed366fca0fbf0f78effebb7e9dcfc7f35883ac46bc927
 *   ground truth: _1653_map_groundtruth_rc444.ndjson (srmech 0.9.0rc444,
 *   shipped-op cross-check True)
 *
 * PM_K4_CHAIN carries klein4_from_one's variant-"rest" map step VERBATIM
 * (step index 9; 19 body steps, 8 binds), preceded by
 * nine JSON nulls standing for steps 0..8 — the render / sha256 / concat
 * stages this map arm does not claim. PM_K4_CTX pre-seeds those steps'
 * MEASURED outputs (step[7] = the block-0 digest as ASCII bytes,
 * step[8] = the 64-entry j-div-4 table) so the root frame RESUMES the
 * shipped chain at its map step.
 */

static const char PM_K4_CHAIN[] =
    "{\"name\":\"klein4_from_one\",\"steps\":[null,null,null,null,nul"
    "l,null,null,null,null,{\"bind\":{\"divt\":[0,1,0,1],\"frame14\":"
    "[1,1,2,2,2,2,3,3,3,3,3,3,3,3],\"hexb\":\"@step[7].output\",\"hex"
    "val\":[0,1,2,3,4,5,6,7,8,9,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0"
    ",0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,10,11,12,13,14,15],\"jd"
    "iv4\":\"@step[8].output\",\"nibdiv4\":[0,0,0,0,1,1,1,1,2,2,2,2,3"
    ",3,3,3],\"offt\":[1,1,0,0],\"xor4\":[[0,1,2,3],[1,0,3,2],[2,3,0,"
    "1],[3,2,1,0]]},\"body\":[{\"args\":{\"i\":\"@idx.j\",\"seq\":\"@"
    "bind.jdiv4\"},\"class\":\"E\",\"op\":\"srmech.cascade.leaves.seq"
    "_get\"},{\"args\":{\"a\":\"@idx.j\",\"b\":0,\"n\":4},\"class\":\""
    "I\",\"op\":\"mod_add\"},{\"args\":{\"i\":\"@step[1].output\",\"s"
    "eq\":\"@bind.offt\"},\"class\":\"E\",\"op\":\"srmech.cascade.lea"
    "ves.seq_get\"},{\"args\":{\"a\":\"@step[0].output\",\"b\":2,\"n\""
    ":257},\"class\":\"I\",\"op\":\"mod_mul\"},{\"args\":{\"a\":\"@st"
    "ep[3].output\",\"b\":\"@step[2].output\",\"n\":257},\"class\":\""
    "I\",\"op\":\"mod_add\"},{\"args\":{\"a\":\"@step[4].output\",\"b"
    "\":1,\"n\":257},\"class\":\"I\",\"op\":\"mod_add\"},{\"args\":{\""
    "data\":\"@bind.hexb\",\"start\":\"@step[4].output\",\"stop\":\"@"
    "step[5].output\"},\"class\":\"B\",\"op\":\"srmech.cascade.leaves"
    ".byte_slice\"},{\"args\":{\"data\":\"@step[6].output\"},\"class\""
    ":\"B\",\"op\":\"srmech.cascade.leaves.int_parse_le\"},{\"args\":"
    "{\"a\":\"@step[7].output\",\"b\":209,\"n\":257},\"class\":\"I\","
    "\"op\":\"mod_add\"},{\"args\":{\"i\":\"@step[8].output\",\"seq\""
    ":\"@bind.hexval\"},\"class\":\"E\",\"op\":\"srmech.cascade.leave"
    "s.seq_get\"},{\"args\":{\"a\":\"@step[9].output\",\"b\":0,\"n\":"
    "4},\"class\":\"I\",\"op\":\"mod_add\"},{\"args\":{\"i\":\"@step["
    "9].output\",\"seq\":\"@bind.nibdiv4\"},\"class\":\"E\",\"op\":\""
    "srmech.cascade.leaves.seq_get\"},{\"args\":{\"first\":\"@step[10"
    "].output\",\"second\":\"@step[11].output\"},\"class\":\"B\",\"op"
    "\":\"srmech.cascade.leaves.pair\"},{\"args\":{\"i\":\"@step[1].o"
    "utput\",\"seq\":\"@bind.divt\"},\"class\":\"E\",\"op\":\"srmech."
    "cascade.leaves.seq_get\"},{\"args\":{\"i\":\"@step[13].output\","
    "\"seq\":\"@step[12].output\"},\"class\":\"E\",\"op\":\"srmech.ca"
    "scade.leaves.seq_get\"},{\"args\":{\"a\":\"@idx.j\",\"b\":0,\"n\""
    ":14},\"class\":\"I\",\"op\":\"mod_add\"},{\"args\":{\"i\":\"@ste"
    "p[15].output\",\"seq\":\"@bind.frame14\"},\"class\":\"C\",\"op\""
    ":\"srmech.cascade.leaves.seq_get\"},{\"args\":{\"i\":\"@step[14]"
    ".output\",\"seq\":\"@bind.xor4\"},\"class\":\"C\",\"op\":\"srmec"
    "h.cascade.leaves.seq_get\"},{\"args\":{\"i\":\"@step[16].output\""
    ",\"seq\":\"@step[17].output\"},\"class\":\"C\",\"op\":\"srmech.c"
    "ascade.leaves.seq_get\"}],\"index\":\"j\",\"map_over\":\"@step[8"
    "].output\"}],\"variant\":\"rest\"}"
    ;

static const char PM_K4_CTX[] =
    "{\"inputs\":{},\"pre\":[null,null,null,null,null,null,null,\"a6a"
    "8e26568ca872670d49f75caeb60ed20eb07a779d10d5d8021407f6b10b2c9\","
    "[0,0,0,0,1,1,1,1,2,2,2,2,3,3,3,3,4,4,4,4,5,5,5,5,6,6,6,6,7,7,7,7"
    ",8,8,8,8,9,9,9,9,10,10,10,10,11,11,11,11,12,12,12,12,13,13,13,13"
    ",14,14,14,14,15,15,15,15]],\"row\":null}"
    ;

/* The value the SHIPPED Python projection returns for inputs {"sigma": 1, "terms": 24, "theta_den": 1, "theta_num": 1}. */
static const int64_t PM_K4_EXPECT[64] = {
    3, 0, 0, 0, 2, 0, 1, 1, 1, 3, 1, 0, 2, 2, 3, 0,
    2, 0, 0, 3, 1, 1, 3, 0, 0, 2, 3, 1, 3, 0, 0, 2,
    2, 2, 0, 2, 3, 2, 2, 0, 0, 0, 0, 3, 3, 3, 1, 3,
    1, 1, 3, 0, 0, 1, 1, 0, 1, 1, 0, 3, 3, 1, 1, 0
};
