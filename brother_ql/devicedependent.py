
models = [
  'QL-500',
  'QL-550',
  'QL-560',
  'QL-570',
  'QL-580N',
  'QL-650TD',
  'QL-700',
  'QL-710W',
  'QL-720NW',
  'QL-1050',
  'QL-1060N',
]

min_max_length_dots = {
  'default':  (295, 11811),

  # Those are using the default:
  # QL-500 QL-550 QL-560 QL-650TD

  'QL-1050':  (295, 35433),
  'QL-1060N': (295, 35433),

  'QL-570':   (150, 11811),
  'QL-580N':  (150, 11811),
  'QL-700':   (150, 11811),
  'QL-710W':  (150, 11811),
  'QL-720NW': (150, 11811),
}

min_max_feed = {
  'default':  (35, 1500),
}


label_sizes = [
  "12",
  "29",
  "38",
  "50",
  "54",
  "62",
  "102",
  "17x54",
  "17x87",
  "23x23",
  "29x42",
  "29x90",
  "39x90",
  "39x48",
  "52x29",
  "62x29",
  "62x100",
  "102x51",
  "102x152",
  "d12",
  "d24",
  "d58",
]

# label_types
DIE_CUT_LABEL       = 1
ENDLESS_LABEL       = 2
ROUND_DIE_CUT_LABEL = 3

label_type_specs = {
  #                                            (width, length)
  "12":     {'kind': ENDLESS_LABEL, 'tape_size': ( 12,   0), 'dots_total': ( 142,    0), 'dots_printable': ( 106,   0),  'right_margin_dots': 29, 'restrict_printers': []},
  "29":     {'kind': ENDLESS_LABEL, 'tape_size': ( 29,   0), 'dots_total': ( 342,    0), 'dots_printable': ( 306,   0),  'right_margin_dots':  6, 'restrict_printers': []},
  "38":     {'kind': ENDLESS_LABEL, 'tape_size': ( 38,   0), 'dots_total': ( 449,    0), 'dots_printable': ( 413,   0),  'right_margin_dots': 12, 'restrict_printers': []},
  "50":     {'kind': ENDLESS_LABEL, 'tape_size': ( 50,   0), 'dots_total': ( 590,    0), 'dots_printable': ( 554,   0),  'right_margin_dots': 12, 'restrict_printers': []},
  "54":     {'kind': ENDLESS_LABEL, 'tape_size': ( 54,   0), 'dots_total': ( 636,    0), 'dots_printable': ( 590,   0),  'right_margin_dots':  0, 'restrict_printers': []},
  "62":     {'kind': ENDLESS_LABEL, 'tape_size': ( 62,   0), 'dots_total': ( 732,    0), 'dots_printable': ( 696,   0),  'right_margin_dots': 12, 'restrict_printers': []},
  "102":    {'kind': ENDLESS_LABEL, 'tape_size': (102,   0), 'dots_total': (1200,    0), 'dots_printable': (1164,   0),  'right_margin_dots': 12, 'restrict_printers': ['QL-1060N', 'QL-1050']},
  "17x54":  {'kind': DIE_CUT_LABEL, 'tape_size': ( 17,  54), 'dots_total': ( 201,  636), 'dots_printable': ( 165,  566), 'right_margin_dots':  0, 'restrict_printers': []},
  "17x87":  {'kind': DIE_CUT_LABEL, 'tape_size': ( 17,  87), 'dots_total': ( 201, 1026), 'dots_printable': ( 165,  956), 'right_margin_dots':  0, 'restrict_printers': []},
  "23x23":  {'kind': DIE_CUT_LABEL, 'tape_size': ( 23,  23), 'dots_total': ( 272,  272), 'dots_printable': ( 202,  202), 'right_margin_dots': 42, 'restrict_printers': []},
  "29x42":  {'kind': DIE_CUT_LABEL, 'tape_size': ( 29,  42), 'dots_total': ( 342,  495), 'dots_printable': ( 306,  425), 'right_margin_dots':  6, 'restrict_printers': []},
  "29x90":  {'kind': DIE_CUT_LABEL, 'tape_size': ( 29,  90), 'dots_total': ( 342, 1061), 'dots_printable': ( 306,  991), 'right_margin_dots':  6, 'restrict_printers': []},
  "39x90":  {'kind': DIE_CUT_LABEL, 'tape_size': ( 38,  90), 'dots_total': ( 449, 1061), 'dots_printable': ( 413,  991), 'right_margin_dots': 12, 'restrict_printers': []},
  "39x48":  {'kind': DIE_CUT_LABEL, 'tape_size': ( 39,  48), 'dots_total': ( 461,  565), 'dots_printable': ( 425,  495), 'right_margin_dots':  6, 'restrict_printers': []},
  "52x29":  {'kind': DIE_CUT_LABEL, 'tape_size': ( 52,  29), 'dots_total': ( 614,  341), 'dots_printable': ( 578,  271), 'right_margin_dots':  0, 'restrict_printers': []},
  "62x29":  {'kind': DIE_CUT_LABEL, 'tape_size': ( 62,  29), 'dots_total': ( 732,  341), 'dots_printable': ( 696,  271), 'right_margin_dots': 12, 'restrict_printers': []},
  "62x100": {'kind': DIE_CUT_LABEL, 'tape_size': ( 62, 100), 'dots_total': ( 732, 1179), 'dots_printable': ( 696, 1109), 'right_margin_dots': 12, 'restrict_printers': []},
  "102x51": {'kind': DIE_CUT_LABEL, 'tape_size': (102,  51), 'dots_total': (1200,  596), 'dots_printable': (1164,  526), 'right_margin_dots': 12, 'restrict_printers': ['QL-1060N', 'QL-1050']},
  "102x152":{'kind': DIE_CUT_LABEL, 'tape_size': (102, 152), 'dots_total': (1200, 1804), 'dots_printable': (1164, 1660), 'right_margin_dots': 12, 'restrict_printers': ['QL-1060N', 'QL-1050']},
  "d12":    {'kind': ROUND_DIE_CUT_LABEL,'tape_size':(12,-1),'dots_total': ( 142,  142), 'dots_printable': (  94,   94), 'right_margin_dots':113, 'restrict_printers': []},
  "d24":    {'kind': ROUND_DIE_CUT_LABEL,'tape_size':(24,-1),'dots_total': ( 284,  284), 'dots_printable': ( 236,  236), 'right_margin_dots': 42, 'restrict_printers': []},
  "d58":    {'kind': ROUND_DIE_CUT_LABEL,'tape_size':(58,-1),'dots_total': ( 688,  688), 'dots_printable': ( 618,  618), 'right_margin_dots': 51, 'restrict_printers': []},
}

number_bytes_per_row = {
  'default':   90,
  'QL-1050':  162,
  'QL-1060N': 162,
}

right_margin_addition = {
  'default':   0,
  'QL-1050':  44,
  'QL-1060N': 44,
}

modesetting = [
  'QL-580N',
  'QL-650TD',
  'QL-1050',
  'QL-1060N',
  'QL-710W',
  'QL-720NW',
]

cuttingsupport = [
  'QL-560',
  'QL-570',
  'QL-580N',
  'QL-650TD',
  'QL-700',
  'QL-1050',
  'QL-1060N',
  'QL-710W',
  'QL-720NW',
]

expandedmode = cuttingsupport

compressionsupport = [
  'QL-580N',
  'QL-650TD',
  'QL-1050',
  'QL-1060N',
  'QL-710W',
  'QL-720NW',
]
