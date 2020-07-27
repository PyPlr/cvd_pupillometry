#,-*-,coding:,utf-8,-*-
"""
Created,on,Wed,Jun,,3,09:28:47,2020

@author:,JTM
note:,https://scipython.com/blog/converting-a-spectrum-to-a-colour/
note: http://cvrl.ioo.ucl.ac.uk/cmfs.htm
"""

import numpy as np
import pandas as pd

# The CIE colour matching function for 380 - 780 nm in 5 nm intervals

def get_CIE_CMF(asdf=False):
    
    colnames = ["index", "X", "Y", "Z"]
    
    cmf = np.array([
    380,0.0014,0.0000,0.0065,
    385,0.0022,0.0001,0.0105,
    390,0.0042,0.0001,0.0201,
    395,0.0076,0.0002,0.0362,
    400,0.0143,0.0004,0.0679,
    405,0.0232,0.0006,0.1102,
    410,0.0435,0.0012,0.2074,
    415,0.0776,0.0022,0.3713,
    420,0.1344,0.0040,0.6456,
    425,0.2148,0.0073,1.0391,
    430,0.2839,0.0116,1.3856,
    435,0.3285,0.0168,1.6230,
    440,0.3483,0.0230,1.7471,
    445,0.3481,0.0298,1.7826,
    450,0.3362,0.0380,1.7721,
    455,0.3187,0.0480,1.7441,
    460,0.2908,0.0600,1.6692,
    465,0.2511,0.0739,1.5281,
    470,0.1954,0.0910,1.2876,
    475,0.1421,0.1126,1.0419,
    480,0.0956,0.1390,0.8130,
    485,0.0580,0.1693,0.6162,
    490,0.0320,0.2080,0.4652,
    495,0.0147,0.2586,0.3533,
    500,0.0049,0.3230,0.2720,
    505,0.0024,0.4073,0.2123,
    510,0.0093,0.5030,0.1582,
    515,0.0291,0.6082,0.1117,
    520,0.0633,0.7100,0.0782,
    525,0.1096,0.7932,0.0573,
    530,0.1655,0.8620,0.0422,
    535,0.2257,0.9149,0.0298,
    540,0.2904,0.9540,0.0203,
    545,0.3597,0.9803,0.0134,
    550,0.4334,0.9950,0.0087,
    555,0.5121,1.0000,0.0057,
    560,0.5945,0.9950,0.0039,
    565,0.6784,0.9786,0.0027,
    570,0.7621,0.9520,0.0021,
    575,0.8425,0.9154,0.0018,
    580,0.9163,0.8700,0.0017,
    585,0.9786,0.8163,0.0014,
    590,1.0263,0.7570,0.0011,
    595,1.0567,0.6949,0.0010,
    600,1.0622,0.6310,0.0008,
    605,1.0456,0.5668,0.0006,
    610,1.0026,0.5030,0.0003,
    615,0.9384,0.4412,0.0002,
    620,0.8544,0.3810,0.0002,
    625,0.7514,0.3210,0.0001,
    630,0.6424,0.2650,0.0000,
    635,0.5419,0.2170,0.0000,
    640,0.4479,0.1750,0.0000,
    645,0.3608,0.1382,0.0000,
    650,0.2835,0.1070,0.0000,
    655,0.2187,0.0816,0.0000,
    660,0.1649,0.0610,0.0000,
    665,0.1212,0.0446,0.0000,
    670,0.0874,0.0320,0.0000,
    675,0.0636,0.0232,0.0000,
    680,0.0468,0.0170,0.0000,
    685,0.0329,0.0119,0.0000,
    690,0.0227,0.0082,0.0000,
    695,0.0158,0.0057,0.0000,
    700,0.0114,0.0041,0.0000,
    705,0.0081,0.0029,0.0000,
    710,0.0058,0.0021,0.0000,
    715,0.0041,0.0015,0.0000,
    720,0.0029,0.0010,0.0000,
    725,0.0020,0.0007,0.0000,
    730,0.0014,0.0005,0.0000,
    735,0.0010,0.0004,0.0000,
    740,0.0007,0.0002,0.0000,
    745,0.0005,0.0002,0.0000,
    750,0.0003,0.0001,0.0000,
    755,0.0002,0.0001,0.0000,
    760,0.0002,0.0001,0.0000,
    765,0.0001,0.0000,0.0000,
    770,0.0001,0.0000,0.0000,
    775,0.0001,0.0000,0.0000,
    780,0.0000,0.0000,0.0000
    ]).reshape(81,4).astype(np.float64)
    
    if asdf:
        cmf.reshape(81,4).astype(np.float64)
        cmf = pd.DataFrame(data=cmf, columns=colnames)
        cmf.set_index("index", inplace=True)
    else:
        cmf = cmf.reshape(81,4).astype(np.float64).T
        
    return cmf

def get_CIES026(asdf=False):
    
    colnames = ["index","S","M","L","Rods","Mel"]
    
    T_cies026 = np.array([
    380,np.nan,np.nan,np.nan,0.000589,0.00091816,
    381,np.nan,np.nan,np.nan,0.000665,0.0010456,
    382,np.nan,np.nan,np.nan,0.000752,0.0011786,
    383,np.nan,np.nan,np.nan,0.000854,0.0013228,
    384,np.nan,np.nan,np.nan,0.000972,0.0014838,
    385,np.nan,np.nan,np.nan,0.001108,0.0016672,
    386,np.nan,np.nan,np.nan,0.001268,0.001881,
    387,np.nan,np.nan,np.nan,0.001453,0.0021299,
    388,np.nan,np.nan,np.nan,0.001668,0.0024146,
    389,np.nan,np.nan,np.nan,0.001918,0.0027358,
    390,0.0061427,0.00035823,0.00040762,0.002209,0.0030944,
    391,0.0074428,0.00043866,0.00049707,0.002547,0.0035071,
    392,0.0090166,0.00053623,0.00060471,0.002939,0.0039908,
    393,0.010917,0.00065406,0.00073364,0.003394,0.0045468,
    394,0.013205,0.00079565,0.00088725,0.003921,0.0051763,
    395,0.015952,0.00096483,0.0010692,0.00453,0.0058804,
    396,0.019235,0.0011657,0.0012834,0.00524,0.0066933,
    397,0.023144,0.0014026,0.0015338,0.00605,0.007651,
    398,0.027775,0.0016799,0.0018244,0.00698,0.0087569,
    399,0.033234,0.0020018,0.002159,0.00806,0.010015,
    400,0.039631,0.0023721,0.0025407,0.00929,0.011428,
    401,0.04708,0.0027943,0.0029728,0.0107,0.013077,
    402,0.055701,0.0032737,0.0034599,0.01231,0.01504,
    403,0.065614,0.0038166,0.0040079,0.01413,0.017317,
    404,0.076932,0.0044302,0.0046237,0.01619,0.019907,
    405,0.089761,0.0051232,0.0053155,0.01852,0.022811,
    406,0.10419,0.0059046,0.0060914,0.02113,0.026319,
    407,0.12027,0.0067801,0.0069529,0.02405,0.030596,
    408,0.13804,0.0077526,0.0078963,0.0273,0.035454,
    409,0.15749,0.0088229,0.008913,0.03089,0.040703,
    410,0.17853,0.0099884,0.0099884,0.03484,0.046155,
    411,0.20108,0.011245,0.011105,0.03916,0.051782,
    412,0.22509,0.012595,0.012261,0.0439,0.05778,
    413,0.25057,0.014042,0.013458,0.049,0.064297,
    414,0.27751,0.015594,0.014704,0.0545,0.07148,
    415,0.30594,0.01726,0.016013,0.0604,0.079477,
    416,0.33586,0.019047,0.017396,0.0668,0.089181,
    417,0.36698,0.020955,0.018845,0.0736,0.10076,
    418,0.39888,0.022976,0.020344,0.0808,0.11326,
    419,0.431,0.025102,0.02187,0.0885,0.12573,
    420,0.46269,0.027316,0.023396,0.0966,0.13724,
    421,0.49336,0.029606,0.024896,0.1052,0.14745,
    422,0.52301,0.031975,0.026376,0.1141,0.15701,
    423,0.55194,0.034433,0.027854,0.1235,0.16646,
    424,0.5806,0.036998,0.029355,0.1334,0.17632,
    425,0.60957,0.039693,0.03091,0.1436,0.1871,
    426,0.63936,0.04254,0.03255,0.1541,0.19921,
    427,0.66965,0.045547,0.034271,0.1651,0.21241,
    428,0.69983,0.048716,0.036062,0.1764,0.22623,
    429,0.72918,0.052047,0.037905,0.1879,0.2402,
    430,0.75689,0.055538,0.039781,0.1998,0.25387,
    431,0.78229,0.059188,0.04167,0.2119,0.26702,
    432,0.80567,0.062982,0.043573,0.2243,0.27998,
    433,0.8276,0.066903,0.045493,0.2369,0.29303,
    434,0.84878,0.070929,0.047439,0.2496,0.3065,
    435,0.86998,0.07503,0.049417,0.2625,0.32068,
    436,0.89176,0.079177,0.051434,0.2755,0.33602,
    437,0.91344,0.083346,0.053474,0.2886,0.35236,
    438,0.93398,0.087516,0.05551,0.3017,0.36913,
    439,0.95222,0.091662,0.057517,0.3149,0.38573,
    440,0.96696,0.095761,0.059462,0.3281,0.40159,
    441,0.97734,0.099798,0.061324,0.3412,0.41647,
    442,0.98403,0.1038,0.063129,0.3543,0.4308,
    443,0.98814,0.10783,0.064919,0.3673,0.44492,
    444,0.99085,0.11195,0.066742,0.3803,0.4592,
    445,0.99334,0.11622,0.068654,0.3931,0.474,
    446,0.99637,0.12071,0.070696,0.406,0.48952,
    447,0.99904,0.12536,0.072851,0.418,0.50552,
    448,0.99998,0.13011,0.075078,0.431,0.52174,
    449,0.99784,0.13486,0.077332,0.443,0.5379,
    450,0.99133,0.13949,0.079565,0.455,0.55371,
    451,0.97966,0.14394,0.081737,0.467,0.5691,
    452,0.96391,0.14828,0.083883,0.479,0.58424,
    453,0.94557,0.15264,0.08606,0.49,0.59928,
    454,0.92608,0.15716,0.088332,0.502,0.61437,
    455,0.90673,0.16201,0.09077,0.513,0.62965,
    456,0.88851,0.16733,0.09344,0.524,0.64519,
    457,0.87135,0.17314,0.096358,0.535,0.66089,
    458,0.855,0.17942,0.09953,0.546,0.67666,
    459,0.8392,0.18612,0.10296,0.557,0.69241,
    460,0.82373,0.1932,0.10666,0.567,0.70805,
    461,0.80831,0.20062,0.11063,0.578,0.72359,
    462,0.79243,0.20832,0.11483,0.588,0.73911,
    463,0.77557,0.21621,0.11922,0.599,0.75456,
    464,0.75724,0.22423,0.12374,0.61,0.76994,
    465,0.73704,0.23228,0.12834,0.62,0.78522,
    466,0.71473,0.24026,0.13295,0.631,0.80068,
    467,0.69056,0.24816,0.13757,0.642,0.81635,
    468,0.66489,0.25599,0.14222,0.653,0.8318,
    469,0.63808,0.26374,0.14691,0.664,0.84659,
    470,0.61046,0.27144,0.15165,0.676,0.86029,
    471,0.58235,0.2791,0.15648,0.687,0.87292,
    472,0.55407,0.28675,0.1614,0.699,0.88487,
    473,0.5259,0.29448,0.16646,0.71,0.89624,
    474,0.49811,0.30232,0.17169,0.722,0.90716,
    475,0.47089,0.31037,0.17712,0.734,0.91773,
    476,0.44445,0.31869,0.18278,0.745,0.92834,
    477,0.41899,0.32731,0.18868,0.757,0.93895,
    478,0.3947,0.33623,0.19484,0.769,0.94903,
    479,0.37171,0.34548,0.20126,0.781,0.95809,
    480,0.35011,0.35507,0.20794,0.793,0.96561,
    481,0.3299,0.36499,0.21488,0.805,0.97198,
    482,0.31086,0.37514,0.22202,0.817,0.97783,
    483,0.29274,0.38541,0.22932,0.828,0.98301,
    484,0.27534,0.39565,0.23668,0.84,0.98733,
    485,0.2585,0.40569,0.24405,0.851,0.99062,
    486,0.24216,0.41543,0.25135,0.862,0.99334,
    487,0.2265,0.42506,0.2587,0.873,0.99589,
    488,0.21173,0.43485,0.26625,0.884,0.99801,
    489,0.19796,0.4451,0.2742,0.894,0.99946,
    490,0.1853,0.45614,0.28275,0.904,1,
    491,0.17375,0.46824,0.29207,0.914,0.99956,
    492,0.16315,0.48125,0.30209,0.923,0.99836,
    493,0.15331,0.49493,0.31267,0.932,0.99659,
    494,0.14409,0.50895,0.32364,0.941,0.99442,
    495,0.13535,0.52297,0.33479,0.949,0.99202,
    496,0.12701,0.5367,0.34594,0.957,0.98879,
    497,0.11902,0.55019,0.35713,0.964,0.98422,
    498,0.11133,0.56362,0.36842,0.97,0.97866,
    499,0.10393,0.57715,0.37991,0.976,0.97245,
    500,0.096799,0.591,0.39171,0.982,0.96595,
    501,0.089917,0.60535,0.40391,0.986,0.95884,
    502,0.083288,0.62016,0.4165,0.99,0.95072,
    503,0.076916,0.63534,0.42945,0.994,0.94178,
    504,0.070805,0.6508,0.44272,0.997,0.93224,
    505,0.064961,0.6664,0.45625,0.998,0.9223,
    506,0.059405,0.68205,0.47,1,0.91183,
    507,0.054208,0.69767,0.48393,1,0.9006,
    508,0.049428,0.71319,0.49801,1,0.88866,
    509,0.045099,0.72853,0.51223,0.998,0.87607,
    510,0.041234,0.74361,0.52654,0.997,0.86289,
    511,0.037814,0.7584,0.54092,0.994,0.8488,
    512,0.034763,0.77297,0.55541,0.99,0.83368,
    513,0.032003,0.78746,0.57003,0.986,0.81783,
    514,0.029475,0.80202,0.58483,0.981,0.80158,
    515,0.02713,0.81681,0.59987,0.975,0.78523,
    516,0.024938,0.83192,0.61516,0.968,0.76872,
    517,0.022893,0.8471,0.63057,0.961,0.75181,
    518,0.020996,0.86197,0.64588,0.953,0.73459,
    519,0.019243,0.87615,0.66088,0.944,0.71717,
    520,0.01763,0.88921,0.67531,0.935,0.69963,
    521,0.01615,0.90081,0.68898,0.925,0.68189,
    522,0.014791,0.91101,0.70189,0.915,0.66388,
    523,0.013541,0.91997,0.71414,0.904,0.64572,
    524,0.012388,0.92789,0.72584,0.892,0.62753,
    525,0.011325,0.93498,0.73711,0.88,0.60942,
    526,0.010344,0.94141,0.74805,0.867,0.59134,
    527,0.0094409,0.94728,0.75868,0.854,0.57321,
    528,0.0086137,0.95262,0.76903,0.84,0.5551,
    529,0.0078583,0.9575,0.7791,0.826,0.53711,
    530,0.0071709,0.96196,0.7889,0.811,0.51931,
    531,0.0065465,0.96608,0.79847,0.796,0.50165,
    532,0.0059778,0.96997,0.80795,0.781,0.48407,
    533,0.0054579,0.97374,0.81748,0.765,0.46664,
    534,0.0049812,0.97754,0.82724,0.749,0.44944,
    535,0.0045429,0.98148,0.8374,0.733,0.43253,
    536,0.0041391,0.98563,0.84808,0.717,0.41586,
    537,0.0037679,0.98975,0.85906,0.7,0.39937,
    538,0.0034278,0.99355,0.87007,0.683,0.38314,
    539,0.003117,0.99671,0.88078,0.667,0.36722,
    540,0.0028335,0.99893,0.89087,0.65,0.35171,
    541,0.0025756,0.99994,0.90006,0.633,0.33654,
    542,0.0023408,0.99969,0.90825,0.616,0.32165,
    543,0.0021272,0.99818,0.91543,0.599,0.30708,
    544,0.0019328,0.9954,0.92158,0.581,0.2929,
    545,0.0017557,0.99138,0.92666,0.564,0.27914,
    546,0.0015945,0.9862,0.93074,0.548,0.26574,
    547,0.0014478,0.98023,0.93416,0.531,0.25265,
    548,0.0013143,0.97391,0.93732,0.514,0.23992,
    549,0.0011928,0.96765,0.94063,0.497,0.22759,
    550,0.0010823,0.96188,0.94453,0.481,0.21572,
    551,0.00098182,0.95682,0.94929,0.465,0.20424,
    552,0.00089053,0.95215,0.95468,0.448,0.19307,
    553,0.00080769,0.9474,0.96031,0.433,0.18229,
    554,0.00073257,0.9421,0.96579,0.417,0.17193,
    555,0.00066451,0.93583,0.9707,0.402,0.16206,
    556,0.00060289,0.92827,0.97476,0.3864,0.1526,
    557,0.00054706,0.91967,0.97806,0.3715,0.14349,
    558,0.00049646,0.91036,0.98082,0.3569,0.13475,
    559,0.00045057,0.90068,0.98327,0.3427,0.12642,
    560,0.00040893,0.89095,0.98564,0.3288,0.11853,
    561,0.00037114,0.88139,0.98808,0.3151,0.11101,
    562,0.00033684,0.87183,0.99056,0.3018,0.10379,
    563,0.00030572,0.86206,0.99294,0.2888,0.096921,
    564,0.0002775,0.85184,0.99512,0.2762,0.090426,
    565,0.00025192,0.84097,0.99698,0.2639,0.084346,
    566,0.00022872,0.8293,0.99841,0.2519,0.07862,
    567,0.0002077,0.81691,0.99939,0.2403,0.073175,
    568,0.00018864,0.80391,0.99991,0.2291,0.068029,
    569,0.00017136,0.79041,0.99996,0.2182,0.063198,
    570,0.00015569,0.77653,0.99954,0.2076,0.058701,
    571,0.00014148,0.76231,0.99862,0.1974,0.054483,
    572,0.0001286,0.74767,0.99705,0.1876,0.050489,
    573,0.00011691,0.73248,0.9947,0.1782,0.046734,
    574,0.00010632,0.71662,0.99142,0.169,0.043236,
    575,9.67E-05,0.70001,0.98706,0.1602,0.040009,
    576,8.80E-05,0.68265,0.9816,0.1517,0.03701,
    577,8.01E-05,0.66482,0.97545,0.1436,0.03419,
    578,7.29E-05,0.64686,0.96912,0.1358,0.031556,
    579,6.64E-05,0.62907,0.96309,0.1284,0.029115,
    580,6.05E-05,0.61173,0.95784,0.1212,0.026875,
    581,5.51E-05,0.595,0.95366,0.1143,0.024801,
    582,5.02E-05,0.57878,0.95024,0.1078,0.02286,
    583,4.58E-05,0.56293,0.94709,0.1015,0.021053,
    584,4.18E-05,0.54732,0.94375,0.0956,0.019386,
    585,3.81E-05,0.53182,0.93978,0.0899,0.017862,
    586,3.48E-05,0.51635,0.93483,0.0845,0.016458,
    587,3.18E-05,0.50087,0.92892,0.0793,0.015147,
    588,2.90E-05,0.48535,0.92218,0.0745,0.013931,
    589,2.65E-05,0.46978,0.91473,0.0699,0.012812,
    590,2.43E-05,0.45414,0.90669,0.0655,0.01179,
    591,2.22E-05,0.43845,0.89817,0.0613,0.010849,
    592,2.03E-05,0.42278,0.88919,0.0574,0.0099711,
    593,1.86E-05,0.40719,0.87976,0.0537,0.0091585,
    594,1.70E-05,0.39175,0.86989,0.0502,0.0084124,
    595,1.56E-05,0.37653,0.8596,0.0469,0.0077343,
    596,1.43E-05,0.36156,0.84891,0.0438,0.0071125,
    597,1.31E-05,0.34686,0.83786,0.0409,0.0065348,
    598,1.20E-05,0.33242,0.82652,0.03816,0.0060011,
    599,1.10E-05,0.31826,0.81494,0.03558,0.0055117,
    600,1.01E-05,0.30438,0.80317,0.03315,0.0050669,
    601,9.31E-06,0.29078,0.79125,0.03087,0.0046587,
    602,8.56E-06,0.27751,0.77912,0.02874,0.0042795,
    603,7.87E-06,0.26458,0.76669,0.02674,0.0039294,
    604,7.24E-06,0.25201,0.7539,0.02487,0.0036087,
    605,6.67E-06,0.23984,0.74068,0.02312,0.0033177,
    606,6.14E-06,0.22806,0.72699,0.02147,0.0030511,
    607,5.66E-06,0.2167,0.71291,0.01994,0.0028037,
    608,5.22E-06,0.20575,0.69849,0.01851,0.0025756,
    609,4.81E-06,0.19522,0.68383,0.01718,0.0023667,
    610,4.44E-06,0.1851,0.66899,0.01593,0.002177,
    611,4.10E-06,0.1754,0.65404,0.01477,0.0020032,
    612,3.79E-06,0.16609,0.63898,0.01369,0.0018419,
    613,3.50E-06,0.15717,0.62382,0.01269,0.0016932,
    614,3.24E-06,0.14862,0.60858,0.01175,0.0015569,
    615,2.99E-06,0.14043,0.59325,0.01088,0.0014331,
    616,np.nan,0.13259,0.57786,0.01007,0.0013197,
    617,np.nan,0.12509,0.56249,0.00932,0.0012145,
    618,np.nan,0.11793,0.54725,0.00862,0.0011174,
    619,np.nan,0.11109,0.53221,0.00797,0.0010284,
    620,np.nan,0.10457,0.51745,0.00737,0.00094731,
    621,np.nan,0.098366,0.50299,0.00682,0.00087281,
    622,np.nan,0.092468,0.48869,0.0063,0.00080358,
    623,np.nan,0.086876,0.47438,0.00582,0.00073962,
    624,np.nan,0.081583,0.4599,0.00538,0.00068097,
    625,np.nan,0.076584,0.44512,0.00497,0.00062765,
    626,np.nan,0.071868,0.43001,0.00459,0.00057875,
    627,np.nan,0.067419,0.41469,0.00424,0.00053336,
    628,np.nan,0.063218,0.39934,0.003913,0.00049144,
    629,np.nan,0.059249,0.38412,0.003613,0.00045298,
    630,np.nan,0.055499,0.36917,0.003335,0.00041796,
    631,np.nan,0.051955,0.35458,0.003079,0.00038579,
    632,np.nan,0.04861,0.34039,0.002842,0.00035591,
    633,np.nan,0.045459,0.32661,0.002623,0.00032829,
    634,np.nan,0.042494,0.31325,0.002421,0.00030293,
    635,np.nan,0.03971,0.30032,0.002235,0.0002798,
    636,np.nan,0.037095,0.28782,0.002062,0.00025854,
    637,np.nan,0.034635,0.27576,0.001903,0.00023879,
    638,np.nan,0.032313,0.26416,0.001757,0.00022051,
    639,np.nan,0.030115,0.25301,0.001621,0.0002037,
    640,np.nan,0.028031,0.24232,0.001497,0.00018834,
    641,np.nan,0.026056,0.23206,0.001382,0.00017419,
    642,np.nan,0.024201,0.22216,0.001276,0.00016102,
    643,np.nan,0.022476,0.21252,0.001178,0.00014882,
    644,np.nan,0.020887,0.20306,0.001088,0.00013759,
    645,np.nan,0.019437,0.19373,0.001005,0.00012734,
    646,np.nan,0.01812,0.18449,0.000928,0.00011789,
    647,np.nan,0.016915,0.1754,0.000857,0.0001091,
    648,np.nan,0.015799,0.16651,0.000792,0.00010095,
    649,np.nan,0.014754,0.15787,0.000732,9.34E-05,
    650,np.nan,0.013766,0.14951,0.000677,8.66E-05,
    651,np.nan,0.012825,0.14147,0.000626,8.02E-05,
    652,np.nan,0.01193,0.13376,0.000579,7.43E-05,
    653,np.nan,0.011085,0.12638,0.000536,6.89E-05,
    654,np.nan,0.010289,0.11934,0.000496,6.38E-05,
    655,np.nan,0.0095432,0.11264,0.000459,5.92E-05,
    656,np.nan,0.0088461,0.10626,0.000425,5.49E-05,
    657,np.nan,0.008196,0.10021,0.0003935,5.09E-05,
    658,np.nan,0.0075906,0.094456,0.0003645,4.72E-05,
    659,np.nan,0.0070275,0.088993,0.0003377,4.38E-05,
    660,np.nan,0.0065045,0.083808,0.0003129,4.07E-05,
    661,np.nan,0.0060195,0.078886,0.0002901,3.78E-05,
    662,np.nan,0.0055709,0.074219,0.0002689,3.51E-05,
    663,np.nan,0.0051573,0.069795,0.0002493,3.26E-05,
    664,np.nan,0.0047769,0.065605,0.0002313,3.03E-05,
    665,np.nan,0.0044279,0.061638,0.0002146,2.81E-05,
    666,np.nan,0.0041083,0.057886,0.0001991,2.62E-05,
    667,np.nan,0.0038147,0.054337,0.0001848,2.43E-05,
    668,np.nan,0.0035439,0.050981,0.0001716,2.26E-05,
    669,np.nan,0.0032933,0.04781,0.0001593,2.10E-05,
    670,np.nan,0.0030605,0.044813,0.000148,1.96E-05,
    671,np.nan,0.0028437,0.041983,0.0001375,1.82E-05,
    672,np.nan,0.0026418,0.039311,0.0001277,1.69E-05,
    673,np.nan,0.0024537,0.036789,0.0001187,1.57E-05,
    674,np.nan,0.0022787,0.03441,0.0001104,1.47E-05,
    675,np.nan,0.002116,0.032166,0.0001026,1.36E-05,
    676,np.nan,0.0019646,0.030051,9.54E-05,1.27E-05,
    677,np.nan,0.0018238,0.028059,8.88E-05,1.18E-05,
    678,np.nan,0.0016929,0.026186,8.26E-05,1.10E-05,
    679,np.nan,0.0015712,0.024426,7.69E-05,1.03E-05,
    680,np.nan,0.001458,0.022774,7.15E-05,9.58E-06,
    681,np.nan,0.0013527,0.021224,6.66E-05,8.93E-06,
    682,np.nan,0.0012548,0.019768,6.20E-05,8.33E-06,
    683,np.nan,0.0011634,0.018399,5.78E-05,7.76E-06,
    684,np.nan,0.0010781,0.017109,5.38E-05,7.24E-06,
    685,np.nan,0.00099842,0.015894,5.01E-05,6.75E-06,
    686,np.nan,0.00092396,0.014749,4.67E-05,6.31E-06,
    687,np.nan,0.00085471,0.013677,4.36E-05,5.88E-06,
    688,np.nan,0.00079065,0.01268,4.06E-05,5.49E-06,
    689,np.nan,0.00073168,0.011759,3.79E-05,5.13E-06,
    690,np.nan,0.00067765,0.010912,3.53E-05,4.79E-06,
    691,np.nan,0.0006283,0.010137,3.30E-05,4.47E-06,
    692,np.nan,0.00058311,0.0094257,3.08E-05,4.18E-06,
    693,np.nan,0.00054158,0.0087692,2.87E-05,3.90E-06,
    694,np.nan,0.00050329,0.0081608,2.68E-05,3.65E-06,
    695,np.nan,0.00046787,0.0075945,2.50E-05,3.41E-06,
    696,np.nan,0.00043501,0.0070659,2.34E-05,3.19E-06,
    697,np.nan,0.00040449,0.0065725,2.18E-05,2.98E-06,
    698,np.nan,0.00037614,0.0061126,2.04E-05,2.79E-06,
    699,np.nan,0.00034978,0.0056844,1.91E-05,2.61E-06,
    700,np.nan,0.00032528,0.0052861,1.78E-05,2.44E-06,
    701,np.nan,0.00030248,0.0049157,1.66E-05,2.28E-06,
    702,np.nan,0.00028124,0.0045709,1.56E-05,2.14E-06,
    703,np.nan,0.00026143,0.0042491,1.45E-05,2.00E-06,
    704,np.nan,0.00024293,0.0039483,1.36E-05,1.87E-06,
    705,np.nan,0.00022564,0.0036667,1.27E-05,1.75E-06,
    706,np.nan,0.00020948,0.003403,1.19E-05,1.64E-06,
    707,np.nan,0.0001944,0.0031563,1.11E-05,1.54E-06,
    708,np.nan,0.00018037,0.0029262,1.04E-05,1.44E-06,
    709,np.nan,0.00016735,0.0027121,9.76E-06,1.35E-06,
    710,np.nan,0.00015529,0.0025133,9.14E-06,1.27E-06,
    711,np.nan,0.00014413,0.002329,8.56E-06,1.19E-06,
    712,np.nan,0.00013383,0.0021584,8.02E-06,1.11E-06,
    713,np.nan,0.00012431,0.0020007,7.51E-06,1.04E-06,
    714,np.nan,0.00011551,0.0018552,7.04E-06,9.78E-07,
    715,np.nan,0.00010739,0.0017211,6.60E-06,9.18E-07,
    716,np.nan,9.99E-05,0.0015975,6.18E-06,8.62E-07,
    717,np.nan,9.29E-05,0.0014834,5.80E-06,8.09E-07,
    718,np.nan,8.65E-05,0.0013779,5.44E-06,7.59E-07,
    719,np.nan,8.05E-05,0.00128,5.10E-06,7.12E-07,
    720,np.nan,7.49E-05,0.001189,4.78E-06,6.69E-07,
    721,np.nan,6.98E-05,0.0011043,4.49E-06,6.28E-07,
    722,np.nan,6.49E-05,0.0010256,4.21E-06,5.90E-07,
    723,np.nan,6.05E-05,0.0009526,3.95E-06,5.54E-07,
    724,np.nan,5.63E-05,0.00088496,3.71E-06,5.21E-07,
    725,np.nan,5.25E-05,0.0008224,3.48E-06,4.90E-07,
    726,np.nan,4.89E-05,0.00076459,3.27E-06,4.60E-07,
    727,np.nan,4.56E-05,0.00071111,3.07E-06,4.33E-07,
    728,np.nan,4.25E-05,0.00066157,2.88E-06,4.07E-07,
    729,np.nan,3.97E-05,0.00061561,2.71E-06,3.82E-07,
    730,np.nan,3.70E-05,0.00057292,2.55E-06,3.60E-07,
    731,np.nan,3.46E-05,0.00053321,2.39E-06,3.39E-07,
    732,np.nan,3.23E-05,0.00049623,2.25E-06,3.18E-07,
    733,np.nan,3.01E-05,0.00046178,2.12E-06,3.00E-07,
    734,np.nan,2.81E-05,0.00042965,1.99E-06,2.82E-07,
    735,np.nan,2.62E-05,0.00039967,1.87E-06,2.65E-07,
    736,np.nan,2.45E-05,0.00037169,1.76E-06,2.50E-07,
    737,np.nan,2.28E-05,0.00034565,1.66E-06,2.35E-07,
    738,np.nan,2.13E-05,0.00032149,1.56E-06,2.22E-07,
    739,np.nan,1.99E-05,0.00029916,1.47E-06,2.09E-07,
    740,np.nan,1.86E-05,0.00027855,1.38E-06,1.97E-07,
    741,np.nan,1.74E-05,0.00025958,1.30E-06,1.85E-07,
    742,np.nan,1.63E-05,0.00024206,1.22E-06,1.75E-07,
    743,np.nan,1.53E-05,0.00022581,1.15E-06,1.65E-07,
    744,np.nan,1.43E-05,0.00021067,1.08E-06,1.55E-07,
    745,np.nan,1.34E-05,0.00019653,1.02E-06,1.46E-07,
    746,np.nan,1.25E-05,0.00018327,9.62E-07,1.38E-07,
    747,np.nan,1.17E-05,0.00017087,9.07E-07,1.30E-07,
    748,np.nan,1.10E-05,0.00015929,8.55E-07,1.23E-07,
    749,np.nan,1.03E-05,0.00014851,8.06E-07,1.16E-07,
    750,np.nan,9.63E-06,0.00013848,7.60E-07,1.09E-07,
    751,np.nan,9.02E-06,0.00012918,7.16E-07,1.03E-07,
    752,np.nan,8.45E-06,0.00012054,6.75E-07,9.74E-08,
    753,np.nan,7.92E-06,0.00011252,6.37E-07,9.19E-08,
    754,np.nan,7.43E-06,0.00010506,6.01E-07,8.68E-08,
    755,np.nan,6.97E-06,9.81E-05,5.67E-07,8.20E-08,
    756,np.nan,6.53E-06,9.17E-05,5.35E-07,7.74E-08,
    757,np.nan,6.13E-06,8.56E-05,5.05E-07,7.31E-08,
    758,np.nan,5.75E-06,8.00E-05,4.77E-07,6.91E-08,
    759,np.nan,5.40E-06,7.48E-05,4.50E-07,6.53E-08,
    760,np.nan,5.07E-06,6.99E-05,4.25E-07,6.17E-08,
    761,np.nan,4.75E-06,6.53E-05,4.01E-07,5.83E-08,
    762,np.nan,4.46E-06,6.10E-05,3.79E-07,5.51E-08,
    763,np.nan,4.18E-06,5.70E-05,3.58E-07,5.21E-08,
    764,np.nan,3.93E-06,5.33E-05,3.38E-07,4.93E-08,
    765,np.nan,3.69E-06,4.98E-05,3.20E-07,4.66E-08,
    766,np.nan,3.46E-06,4.66E-05,3.02E-07,4.41E-08,
    767,np.nan,3.25E-06,4.36E-05,2.86E-07,4.17E-08,
    768,np.nan,3.05E-06,4.09E-05,2.70E-07,3.94E-08,
    769,np.nan,2.87E-06,3.82E-05,2.55E-07,3.73E-08,
    770,np.nan,2.70E-06,3.58E-05,2.41E-07,3.53E-08,
    771,np.nan,2.53E-06,3.35E-05,2.28E-07,3.34E-08,
    772,np.nan,2.38E-06,3.13E-05,2.16E-07,3.17E-08,
    773,np.nan,2.23E-06,2.93E-05,2.04E-07,3.00E-08,
    774,np.nan,2.09E-06,2.74E-05,1.93E-07,2.84E-08,
    775,np.nan,1.97E-06,2.56E-05,1.83E-07,2.69E-08,
    776,np.nan,1.85E-06,2.40E-05,1.73E-07,2.55E-08,
    777,np.nan,1.74E-06,2.25E-05,1.64E-07,2.42E-08,
    778,np.nan,1.64E-06,2.11E-05,1.55E-07,2.29E-08,
    779,np.nan,1.55E-06,1.98E-05,1.47E-07,2.17E-08,
    780,np.nan,1.46E-06,1.86E-05,1.39E-07,2.05E-08
    ])
    
    S_cies026 = np.array([380, 1, 401])
    
    if asdf:
        T_cies026 = T_cies026.reshape(401,6).astype(np.float64)
        T_cies026 = pd.DataFrame(data=T_cies026, columns=colnames)
        T_cies026.set_index("index", inplace=True)
    else:
        T_cies026 = T_cies026.reshape(401,6).astype(np.float64).T
        
    return S_cies026, T_cies026

def get_CIE_1924_photopic_vl(asdf=False):
    
    colnames = ['index', 'vl']
    
    vl = np.array([
    380, 0.0000390000000,
    381, 0.0000428264000,
    382, 0.0000469146000,
    383, 0.0000515896000,
    384, 0.0000571764000,
    385, 0.0000640000000,
    386, 0.0000723442100,
    387, 0.0000822122400,
    388, 0.0000935081600,
    389, 0.0001061361000,
    390, 0.0001200000000,
    391, 0.0001349840000,
    392, 0.0001514920000,
    393, 0.0001702080000,
    394, 0.0001918160000,
    395, 0.0002170000000,
    396, 0.0002469067000,
    397, 0.0002812400000,
    398, 0.0003185200000,
    399, 0.0003572667000,
    400, 0.0003960000000,
    401, 0.0004337147000,
    402, 0.0004730240000,
    403, 0.0005178760000,
    404, 0.0005722187000,
    405, 0.0006400000000,
    406, 0.0007245600000,
    407, 0.0008255000000,
    408, 0.0009411600000,
    409, 0.0010698800000,
    410, 0.0012100000000,
    411, 0.0013620910000,
    412, 0.0015307520000,
    413, 0.0017203680000,
    414, 0.0019353230000,
    415, 0.0021800000000,
    416, 0.0024548000000,
    417, 0.0027640000000,
    418, 0.0031178000000,
    419, 0.0035264000000,
    420, 0.0040000000000,
    421, 0.0045462400000,
    422, 0.0051593200000,
    423, 0.0058292800000,
    424, 0.0065461600000,
    425, 0.0073000000000,
    426, 0.0080865070000,
    427, 0.0089087200000,
    428, 0.0097676800000,
    429, 0.0106644300000,
    430, 0.0116000000000,
    431, 0.0125731700000,
    432, 0.0135827200000,
    433, 0.0146296800000,
    434, 0.0157150900000,
    435, 0.0168400000000,
    436, 0.0180073600000,
    437, 0.0192144800000,
    438, 0.0204539200000,
    439, 0.0217182400000,
    440, 0.0230000000000,
    441, 0.0242946100000,
    442, 0.0256102400000,
    443, 0.0269585700000,
    444, 0.0283512500000,
    445, 0.0298000000000,
    446, 0.0313108300000,
    447, 0.0328836800000,
    448, 0.0345211200000,
    449, 0.0362257100000,
    450, 0.0380000000000,
    451, 0.0398466700000,
    452, 0.0417680000000,
    453, 0.0437660000000,
    454, 0.0458426700000,
    455, 0.0480000000000,
    456, 0.0502436800000,
    457, 0.0525730400000,
    458, 0.0549805600000,
    459, 0.0574587200000,
    460, 0.0600000000000,
    461, 0.0626019700000,
    462, 0.0652775200000,
    463, 0.0680420800000,
    464, 0.0709110900000,
    465, 0.0739000000000,
    466, 0.0770160000000,
    467, 0.0802664000000,
    468, 0.0836668000000,
    469, 0.0872328000000,
    470, 0.0909800000000,
    471, 0.0949175500000,
    472, 0.0990458400000,
    473, 0.1033674000000,
    474, 0.1078846000000,
    475, 0.1126000000000,
    476, 0.1175320000000,
    477, 0.1226744000000,
    478, 0.1279928000000,
    479, 0.1334528000000,
    480, 0.1390200000000,
    481, 0.1446764000000,
    482, 0.1504693000000,
    483, 0.1564619000000,
    484, 0.1627177000000,
    485, 0.1693000000000,
    486, 0.1762431000000,
    487, 0.1835581000000,
    488, 0.1912735000000,
    489, 0.1994180000000,
    490, 0.2080200000000,
    491, 0.2171199000000,
    492, 0.2267345000000,
    493, 0.2368571000000,
    494, 0.2474812000000,
    495, 0.2586000000000,
    496, 0.2701849000000,
    497, 0.2822939000000,
    498, 0.2950505000000,
    499, 0.3085780000000,
    500, 0.3230000000000,
    501, 0.3384021000000,
    502, 0.3546858000000,
    503, 0.3716986000000,
    504, 0.3892875000000,
    505, 0.4073000000000,
    506, 0.4256299000000,
    507, 0.4443096000000,
    508, 0.4633944000000,
    509, 0.4829395000000,
    510, 0.5030000000000,
    511, 0.5235693000000,
    512, 0.5445120000000,
    513, 0.5656900000000,
    514, 0.5869653000000,
    515, 0.6082000000000,
    516, 0.6293456000000,
    517, 0.6503068000000,
    518, 0.6708752000000,
    519, 0.6908424000000,
    520, 0.7100000000000,
    521, 0.7281852000000,
    522, 0.7454636000000,
    523, 0.7619694000000,
    524, 0.7778368000000,
    525, 0.7932000000000,
    526, 0.8081104000000,
    527, 0.8224962000000,
    528, 0.8363068000000,
    529, 0.8494916000000,
    530, 0.8620000000000,
    531, 0.8738108000000,
    532, 0.8849624000000,
    533, 0.8954936000000,
    534, 0.9054432000000,
    535, 0.9148501000000,
    536, 0.9237348000000,
    537, 0.9320924000000,
    538, 0.9399226000000,
    539, 0.9472252000000,
    540, 0.9540000000000,
    541, 0.9602561000000,
    542, 0.9660074000000,
    543, 0.9712606000000,
    544, 0.9760225000000,
    545, 0.9803000000000,
    546, 0.9840924000000,
    547, 0.9874182000000,
    548, 0.9903128000000,
    549, 0.9928116000000,
    550, 0.9949501000000,
    551, 0.9967108000000,
    552, 0.9980983000000,
    553, 0.9991120000000,
    554, 0.9997482000000,
    555, 1.0000000000000,
    556, 0.9998567000000,
    557, 0.9993046000000,
    558, 0.9983255000000,
    559, 0.9968987000000,
    560, 0.9950000000000,
    561, 0.9926005000000,
    562, 0.9897426000000,
    563, 0.9864444000000,
    564, 0.9827241000000,
    565, 0.9786000000000,
    566, 0.9740837000000,
    567, 0.9691712000000,
    568, 0.9638568000000,
    569, 0.9581349000000,
    570, 0.9520000000000,
    571, 0.9454504000000,
    572, 0.9384992000000,
    573, 0.9311628000000,
    574, 0.9234576000000,
    575, 0.9154000000000,
    576, 0.9070064000000,
    577, 0.8982772000000,
    578, 0.8892048000000,
    579, 0.8797816000000,
    580, 0.8700000000000,
    581, 0.8598613000000,
    582, 0.8493920000000,
    583, 0.8386220000000,
    584, 0.8275813000000,
    585, 0.8163000000000,
    586, 0.8047947000000,
    587, 0.7930820000000,
    588, 0.7811920000000,
    589, 0.7691547000000,
    590, 0.7570000000000,
    591, 0.7447541000000,
    592, 0.7324224000000,
    593, 0.7200036000000,
    594, 0.7074965000000,
    595, 0.6949000000000,
    596, 0.6822192000000,
    597, 0.6694716000000,
    598, 0.6566744000000,
    599, 0.6438448000000,
    600, 0.6310000000000,
    601, 0.6181555000000,
    602, 0.6053144000000,
    603, 0.5924756000000,
    604, 0.5796379000000,
    605, 0.5668000000000,
    606, 0.5539611000000,
    607, 0.5411372000000,
    608, 0.5283528000000,
    609, 0.5156323000000,
    610, 0.5030000000000,
    611, 0.4904688000000,
    612, 0.4780304000000,
    613, 0.4656776000000,
    614, 0.4534032000000,
    615, 0.4412000000000,
    616, 0.4290800000000,
    617, 0.4170360000000,
    618, 0.4050320000000,
    619, 0.3930320000000,
    620, 0.3810000000000,
    621, 0.3689184000000,
    622, 0.3568272000000,
    623, 0.3447768000000,
    624, 0.3328176000000,
    625, 0.3210000000000,
    626, 0.3093381000000,
    627, 0.2978504000000,
    628, 0.2865936000000,
    629, 0.2756245000000,
    630, 0.2650000000000,
    631, 0.2547632000000,
    632, 0.2448896000000,
    633, 0.2353344000000,
    634, 0.2260528000000,
    635, 0.2170000000000,
    636, 0.2081616000000,
    637, 0.1995488000000,
    638, 0.1911552000000,
    639, 0.1829744000000,
    640, 0.1750000000000,
    641, 0.1672235000000,
    642, 0.1596464000000,
    643, 0.1522776000000,
    644, 0.1451259000000,
    645, 0.1382000000000,
    646, 0.1315003000000,
    647, 0.1250248000000,
    648, 0.1187792000000,
    649, 0.1127691000000,
    650, 0.1070000000000,
    651, 0.1014762000000,
    652, 0.0961886400000,
    653, 0.0911229600000,
    654, 0.0862648500000,
    655, 0.0816000000000,
    656, 0.0771206400000,
    657, 0.0728255200000,
    658, 0.0687100800000,
    659, 0.0647697600000,
    660, 0.0610000000000,
    661, 0.0573962100000,
    662, 0.0539550400000,
    663, 0.0506737600000,
    664, 0.0475496500000,
    665, 0.0445800000000,
    666, 0.0417587200000,
    667, 0.0390849600000,
    668, 0.0365638400000,
    669, 0.0342004800000,
    670, 0.0320000000000,
    671, 0.0299626100000,
    672, 0.0280766400000,
    673, 0.0263293600000,
    674, 0.0247080500000,
    675, 0.0232000000000,
    676, 0.0218007700000,
    677, 0.0205011200000,
    678, 0.0192810800000,
    679, 0.0181206900000,
    680, 0.0170000000000,
    681, 0.0159037900000,
    682, 0.0148371800000,
    683, 0.0138106800000,
    684, 0.0128347800000,
    685, 0.0119200000000,
    686, 0.0110683100000,
    687, 0.0102733900000,
    688, 0.0095333110000,
    689, 0.0088461570000,
    690, 0.0082100000000,
    691, 0.0076237810000,
    692, 0.0070854240000,
    693, 0.0065914760000,
    694, 0.0061384850000,
    695, 0.0057230000000,
    696, 0.0053430590000,
    697, 0.0049957960000,
    698, 0.0046764040000,
    699, 0.0043800750000,
    700, 0.0041020000000,
    701, 0.0038384530000,
    702, 0.0035890990000,
    703, 0.0033542190000,
    704, 0.0031340930000,
    705, 0.0029290000000,
    706, 0.0027381390000,
    707, 0.0025598760000,
    708, 0.0023932440000,
    709, 0.0022372750000,
    710, 0.0020910000000,
    711, 0.0019535870000,
    712, 0.0018245800000,
    713, 0.0017035800000,
    714, 0.0015901870000,
    715, 0.0014840000000,
    716, 0.0013844960000,
    717, 0.0012912680000,
    718, 0.0012040920000,
    719, 0.0011227440000,
    720, 0.0010470000000,
    721, 0.0009765896000,
    722, 0.0009111088000,
    723, 0.0008501332000,
    724, 0.0007932384000,
    725, 0.0007400000000,
    726, 0.0006900827000,
    727, 0.0006433100000,
    728, 0.0005994960000,
    729, 0.0005584547000,
    730, 0.0005200000000,
    731, 0.0004839136000,
    732, 0.0004500528000,
    733, 0.0004183452000,
    734, 0.0003887184000,
    735, 0.0003611000000,
    736, 0.0003353835000,
    737, 0.0003114404000,
    738, 0.0002891656000,
    739, 0.0002684539000,
    740, 0.0002492000000,
    741, 0.0002313019000,
    742, 0.0002146856000,
    743, 0.0001992884000,
    744, 0.0001850475000,
    745, 0.0001719000000,
    746, 0.0001597781000,
    747, 0.0001486044000,
    748, 0.0001383016000,
    749, 0.0001287925000,
    750, 0.0001200000000,
    751, 0.0001118595000,
    752, 0.0001043224000,
    753, 0.0000973356000,
    754, 0.0000908458700,
    755, 0.0000848000000,
    756, 0.0000791466700,
    757, 0.0000738580000,
    758, 0.0000689160000,
    759, 0.0000643026700,
    760, 0.0000600000000,
    761, 0.0000559818700,
    762, 0.0000522256000,
    763, 0.0000487184000,
    764, 0.0000454474700,
    765, 0.0000424000000,
    766, 0.0000395610400,
    767, 0.0000369151200,
    768, 0.0000344486800,
    769, 0.0000321481600,
    770, 0.0000300000000,
    771, 0.0000279912500,
    772, 0.0000261135600,
    773, 0.0000243602400,
    774, 0.0000227246100,
    775, 0.0000212000000,
    776, 0.0000197785500,
    777, 0.0000184528500,
    778, 0.0000172168700,
    779, 0.0000160645900,
    780, 0.0000149900000
    ])
    
    if asdf:
        vl = vl.reshape(401,2).astype(np.float64)
        vl = pd.DataFrame(data=vl, columns=colnames)
        vl.set_index("index", inplace=True)
    else:
        vl = vl.reshape(401,2).astype(np.float64).T
        
    return vl
