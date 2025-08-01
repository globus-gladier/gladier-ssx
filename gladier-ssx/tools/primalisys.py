from gladier import GladierBaseTool, generate_flow_definition
from typing import Dict, Any

        
def primalisys(**data: Dict[str, Any]) -> None:
    """Analyze PRIME results and generate decision recommendations.
    
    This function scrapes PRIME log files, analyzes various metrics (CC1/2, N_obs, 
    completeness, I**2, I/sigI), fits curves to the data, and generates decision
    recommendations for data quality and processing parameters.
    
    Args:
        data: Dictionary containing the following keys:
            - prime_dir: Path to the prime directory containing log files
            - upload_dir: Path where results will be uploaded
            - prime_input: Path to the prime log file to analyze
            
    Returns:
        None: Results are written to files in the upload directory
    """
    import os
    import numpy as np
    import json
    from scipy.optimize import curve_fit
    import matplotlib.pyplot as plt

    def scrape_log_file(log_fid):
        print('\nIn scrape_log_file')
        postref_dict = {}
        with open(log_fid, 'r') as f:
                #print('in loop 1')
                for line in f:
                    if 'postref_cycle_3' in line:
                        for line in f:
                            if len(line.rstrip()) == 0:
                                break 
                            if '---' in line:
                                continue
                            if 'TOTAL' in line:
                                continue
                            if line.startswith('Bin'):
                                list_of_metrics = line.rstrip().replace('|',' ').split()
                                list_of_metrics.pop(2)
                                #print(list_of_metrics)
                                #print(len(list_of_metrics))
                                for met in list_of_metrics:
                                    postref_dict[met] = []
                            #print(line.rstrip())
                            else:
                                try:
                                    vals = line.rstrip().split()
                                    vals.remove('-')
                                    vals.remove('/')
                                    vals.pop(4)
                                    vals.pop(4)
                                    #print(vals)
                                    #print(vals[1], vals[2])
                                    res = (float(vals[1]) + float(vals[2])) / 2.0
                                    vals.pop(1) 
                                    vals.pop(1) 
                                    vals.insert(1, res)
                                    #print(vals)
                                    #print(len(vals))
                                    for met,val in zip(list_of_metrics,vals):
                                        postref_dict[met].append(val)
                                except:
                                    print('Exception in reading results of line:', line)
                    if 'No. good frames' in line:
                        good = float(line.split(':')[1])
                    if 'No. bad cc frames' in line:
                        bad = float(line.split(':')[1])
        print(good, bad)
        return postref_dict, [good, bad] 

    def power_law(x, a, b):
        return a*np.power(x, b)

    def power_law2(x, a, b, c):
        return (a*np.power(x, -b) + c)

    def ymx(x, a, b):
        return a*x + b

    def exp(x, a, b, c):
        return a * np.exp(-b * x) + c

    def exp2(x, a, b, c, d):
        return d - (a * np.exp(x*b - c))

    def exp3(x, a, b, c):
        return (a * np.exp((x- 20) * b)) + c

    def exp4(x, a, b, c):
        return (a * np.exp(-(x+8) * b)) + c

    def get_index(array, direction, val):
        if direction == 'greater than':
            try:
                result = list(map(lambda k: k < val, array.tolist())).index(True) - 1 
            except:
                result = 19
        elif direction == 'less than':
            try:
                result = list(map(lambda k: k > val, array.tolist())).index(True) - 1
            except:
                result = 19

        return result

    def get_arrays(postref_dict):
        for k,v in postref_dict.items():
            if k == 'Resolution':
                RES = np.array([float(x) for x in v]) 
            if k == '<I**2>':
                I2 = np.array([float(x) for x in v]) 
            if k == 'CC1/2':
                CC = np.array([float(x) for x in v]) 
            if k == '<N_obs>':
                NOBS = np.array([float(x) for x in v]) 
            if k == 'Completeness':
                COMP = np.array([float(x) for x in v]) 
            if k == '<I/sigI>':
                ISIGI = np.array([float(x) for x in v]) 
        return RES, I2, CC, NOBS, COMP, ISIGI

    def fitting(array_list):

        RES, I2, CC, NOBS, COMP, ISIGI = array_list
        res_bins = np.linspace(0,19,20)

        #################
        I2_good = 1.75
        I2_okay = 3.0
        try:
            i2_pars, i2_cov = curve_fit(f=exp3, xdata=res_bins, ydata=I2.copy(), p0=[1, 0.5, 2])
            I2_fit = exp3(res_bins, *i2_pars)
        except:
            I2_fit = np.zeros(20)
            i2_pars, i2_cov = ['fit failed', 0, 2], 0 
        print('i2 pars', i2_pars)
        i2_good_idx = get_index(I2_fit, 'less than', I2_good)
        i2_okay_idx = get_index(I2_fit, 'less than', I2_okay)
        print('i2_okay_idx', i2_okay_idx)
        I2_list = [I2, I2_good, I2_okay, i2_pars, I2_fit, i2_good_idx, i2_okay_idx]

        #################
        CC_good = 50
        CC_okay = 30
        try:
            cc_pars, cc_cov = curve_fit(f=exp, xdata=RES, ydata=CC, p0=[0, 0, 1])
            CC_fit = exp(RES, *cc_pars)
        except:
            CC_fit = np.zeros(20)
            cc_pars, cc_cov = ['fit failed', 0, 0], 0 
        print(cc_pars)
        cc_good_idx = get_index(CC_fit, 'greater than', CC_good)
        cc_okay_idx = get_index(CC_fit, 'greater than', CC_okay)
        print('cc_idx', cc_good_idx)
        print('cc_idx', cc_okay_idx)
        CC_list = [CC, CC_good, CC_okay, cc_pars, CC_fit, cc_good_idx, cc_okay_idx]
        
        ##################
        NOBS_good = 20
        NOBS_okay = 10
        try:
            nobs_pars, nobs_cov = curve_fit(f=exp, xdata=RES, ydata=NOBS, p0=[0, 0, 1])
            NOBS_fit = exp(RES, *nobs_pars)
        except:
            NOBS_fit = np.zeros(20)
            nobs_pars, nobs_cov = ['fit failed', 0, 0], 0 
        print(nobs_pars)
        nobs_good_idx = get_index(NOBS_fit, 'greater than', NOBS_good)
        nobs_okay_idx = get_index(NOBS_fit, 'greater than', NOBS_okay)
        print('nobs_good_indx', nobs_good_idx)
        print('nobs_okay_indx', nobs_okay_idx)
        NOBS_list = [NOBS, NOBS_good, NOBS_okay, nobs_pars, NOBS_fit, nobs_good_idx, nobs_okay_idx]
    
        ################### 
        COMP_good = 100.0 
        COMP_okay = 99.0 
        try:
            comp_pars, comp_cov = curve_fit(f=exp2, xdata=res_bins, ydata=COMP.copy(), p0=[1, 0.2, 2, 100])
            COMP_fit = exp2(res_bins, *comp_pars)
        except:
            COMP_fit = np.zeros(20)
            comp_pars, comp_cov = ['fit failed', 0, 0, 0], 0 
        print(comp_pars)
        comp_good_idx = get_index(COMP_fit, 'greater than', COMP_good)
        comp_okay_idx = get_index(COMP_fit, 'greater than', COMP_okay)
        print('comp_good_idx', comp_good_idx)
        print('comp_okay_idx', comp_okay_idx)
        COMP_list = [COMP, COMP_good, COMP_okay, comp_pars, COMP_fit, comp_good_idx, comp_okay_idx]

        ###########
        ISIGI_good = 0.5
        ISIGI_okay = 0.25
        try:
            isigi_pars, isigi_cov = curve_fit(f=exp4, xdata=res_bins, ydata=ISIGI, p0=[1, 0.6, 4])
            ISIGI_fit = exp4(res_bins, *isigi_pars)
        except:
            ISIGI_fit = np.zeros(20)
            isigi_pars, isigi_cov = ['fit failed', 0, 0], 0 
        print('isigi_pars', isigi_pars)
        isigi_good_idx = get_index(ISIGI_fit, 'greater than', ISIGI_good)
        isigi_okay_idx = get_index(ISIGI_fit, 'greater than', ISIGI_okay)
        print('isigi_good_idx', isigi_good_idx)
        print('isigi_okay_idx', isigi_okay_idx)
        ISIGI_list = [ISIGI, ISIGI_good, ISIGI_okay, isigi_pars, ISIGI_fit, isigi_good_idx, isigi_okay_idx]


        return I2_list, CC_list, NOBS_list, COMP_list, ISIGI_list

    def plot_histograms(postref_dict, gb_list, png_fid):
    
        #Make numpy arrays from dictionary 
        array_list = get_arrays(postref_dict)
        RES, I2, CC, NOBS, COMP, ISIGI = array_list 
    
        #Fit data, find index cutoff, get acceptable metrics
        I2_list, CC_list, NOBS_list, COMP_list, ISIGI_list = fitting(array_list)
        
        [I2,    I2_good,    I2_okay,    i2_pars,    I2_fit,    i2_good_idx,    i2_okay_idx]    = I2_list
        [CC,    CC_good,    CC_okay,    cc_pars,    CC_fit,    cc_good_idx,    cc_okay_idx]    = CC_list
        [NOBS,  NOBS_good,  NOBS_okay,  nobs_pars,  NOBS_fit,  nobs_good_idx,  nobs_okay_idx]  = NOBS_list
        [COMP,  COMP_good,  COMP_okay,  comp_pars,  COMP_fit,  comp_good_idx,  comp_okay_idx]  = COMP_list
        [ISIGI, ISIGI_good, ISIGI_okay, isigi_pars, ISIGI_fit, isigi_good_idx, isigi_okay_idx] = ISIGI_list

        res_bins = np.linspace(0,19,20)
        fig, axs = plt.subplots(2, 3, tight_layout=True, figsize=(12,8.7), facecolor='white' )
        
        res_labels = ['%1.2f'%x for x in RES.tolist()]

        #########################################
        axs[0][0].plot(CC_fit, lw=1, c='k')
        axs[0][0].fill_between(np.linspace(0, cc_good_idx, 20), CC_good, 1000, facecolor='yellowgreen', edgecolor='yellowgreen', alpha=0.6)
        axs[0][0].fill_between(np.linspace(cc_good_idx, cc_okay_idx, 20), CC_good, 1000, facecolor='goldenrod', edgecolor='goldenrod', alpha=0.6)
        axs[0][0].fill_between(np.linspace(0, cc_okay_idx, 20), CC_okay, CC_good, facecolor='goldenrod', edgecolor='goldenrod', alpha=0.6)
        axs[0][0].fill_between(np.linspace(cc_okay_idx, 19, 20), CC_okay, 1000, facecolor='darkred', edgecolor='darkred', alpha=0.6)
        axs[0][0].fill_between(res_bins, 0, CC_okay, facecolor='darkred', edgecolor='darkred', alpha=0.6)

        axs[0][0].plot(CC, lw=4, linestyle='None', c='k', marker='o')
        axs[0][0].set_xticks(res_bins)
        axs[0][0].set_xticklabels(res_labels, rotation=90, fontsize=10)
        axs[0][0].set_xlim(0, 19)
        axs[0][0].set_ylim(np.min(CC),np.max(CC))
        axs[0][0].grid(True)
        axs[0][0].set_title('CC1/2', fontsize=12)

        #########################################
        axs[0][1].plot(NOBS_fit, lw=1, c='k')
        axs[0][1].fill_between(np.linspace(0, nobs_good_idx, 20),NOBS_good, 1000, facecolor='yellowgreen', edgecolor='yellowgreen', alpha=0.6)
        axs[0][1].fill_between(np.linspace(nobs_good_idx, nobs_okay_idx, 20), NOBS_good, 1000, facecolor='goldenrod', edgecolor='goldenrod', alpha=0.6)
        axs[0][1].fill_between(np.linspace(0, nobs_okay_idx, 20), NOBS_okay, NOBS_good, facecolor='goldenrod', edgecolor='goldenrod', alpha=0.6)
        axs[0][1].fill_between(np.linspace(nobs_okay_idx, 19, 20), NOBS_okay, 1000, facecolor='darkred', edgecolor='darkred', alpha=0.6)
        axs[0][1].fill_between(res_bins, 0, NOBS_okay, facecolor='darkred', edgecolor='darkred', alpha=0.6)
        axs[0][1].plot(NOBS, lw=4, linestyle='None', c='k',  marker='o')
        axs[0][1].set_xticks(res_bins)
        axs[0][1].set_xticklabels(res_labels, rotation=90, fontsize=10)
        axs[0][1].set_xlim(0, 19)
        axs[0][1].set_ylim(np.min(NOBS), np.max(NOBS))
        axs[0][1].grid(True)
        axs[0][1].set_title('<N_obs>', fontsize=12)

        #########################################
        axs[0][2].plot(COMP_fit, lw=1, c='k')
        axs[0][2].fill_between(np.linspace(0, comp_okay_idx, 20), COMP_okay, 102, facecolor='yellowgreen', edgecolor='yellowgreen', alpha=0.6)
        axs[0][2].fill_between(np.linspace(comp_okay_idx, 20, 20), 0, 102, facecolor='darkred', edgecolor='darkred', alpha=0.6)
        axs[0][2].fill_between(np.linspace(0, comp_okay_idx, 20), 0, COMP_okay, facecolor='darkred', edgecolor='darkred', alpha=0.6)
        axs[0][2].plot(COMP, lw=4, linestyle='None', c='k', marker='o')
        axs[0][2].set_xticks(res_bins)
        axs[0][2].set_xticklabels(res_labels, rotation=90, fontsize=10)
        axs[0][2].set_xlim(0, 19)
        axs[0][2].set_ylim(np.min(COMP), 101)
        axs[0][2].grid(True)
        axs[0][2].set_title('Completeness', fontsize=12)

        #########################################
        axs[1][0].plot(I2_fit, lw=1, c='k')
        axs[1][0].fill_between(np.linspace(0, i2_okay_idx, 20), I2_okay, I2_good, facecolor='yellowgreen', edgecolor='yellowgreen', alpha=0.6)
        axs[1][0].fill_between(np.linspace(0, i2_okay_idx, 20), I2_okay, np.max(I2), facecolor='darkred', edgecolor='darkred', alpha=0.6)
        axs[1][0].fill_between(np.linspace(0, i2_okay_idx, 20), 0, I2_good, facecolor='darkred', edgecolor='darkred', alpha=0.6)
        axs[1][0].fill_between(np.linspace(i2_okay_idx, 19, 20), 0, np.max(I2), facecolor='darkred', edgecolor='darkred', alpha=0.6)
        axs[1][0].plot(I2, lw=4, linestyle='None', c='k', marker='o')
        axs[1][0].set_xticks(res_bins)
        axs[1][0].set_xticklabels(res_labels, rotation=90, fontsize=10)
        axs[1][0].set_xlim(0, 19)
        axs[1][0].set_ylim(np.min(I2), np.max(I2))
        axs[1][0].grid(True)
        axs[1][0].set_title('<I**2>', fontsize=12)

        #########################################
        axs[1][1].plot(ISIGI_fit, lw=1, c='k')
        axs[1][1].fill_between(np.linspace(0, isigi_good_idx, 20), ISIGI_good, 1000, facecolor='yellowgreen', edgecolor='yellowgreen', alpha=0.6)
        axs[1][1].fill_between(np.linspace(isigi_good_idx, isigi_okay_idx, 20), ISIGI_good, 1000, facecolor='goldenrod', edgecolor='goldenrod', alpha=0.6)
        axs[1][1].fill_between(np.linspace(0, isigi_okay_idx, 20), ISIGI_okay, ISIGI_good, facecolor='goldenrod', edgecolor='goldenrod', alpha=0.6)
        axs[1][1].plot(ISIGI, lw=4, linestyle='None', c='k', marker='o')
        axs[1][1].set_xticks(res_bins)
        axs[1][1].set_xticklabels(res_labels, rotation=90, fontsize=10)
        axs[1][1].set_xlim(0, 19)
        axs[1][1].set_ylim(np.min(ISIGI), np.max(ISIGI))
        axs[1][1].grid(True)
        axs[1][1].set_title('<I/sigI>', fontsize=12)

        #########################################
        n = axs[1][2].pie(gb_list, colors=['yellowgreen','darkred'], explode=(0, 0.1), startangle=0)
        n[0][0].set_alpha(0.6)
        n[0][1].set_alpha(0.6)
        axs[1][2].set_title('Good/Bad frames', fontsize=12)
        plt.savefig(png_fid)
        print(png_fid)
        return RES, I2_list, CC_list, NOBS_list, COMP_list, ISIGI_list

    def decision_engine(fitting_list, gb_list):     
        RES, I2_list, CC_list, NOBS_list, COMP_list, ISIGI_list = fitting_list  
        [I2,    I2_good,     I2_okay,     i2_pars,     I2_fit,     i2_good_idx,     i2_okay_idx]    = I2_list
        [CC,    CC_good,     CC_okay,     cc_pars,     CC_fit,     cc_good_idx,     cc_okay_idx]    = CC_list
        [NOBS,  NOBS_good,   NOBS_okay,   nobs_pars,   NOBS_fit,   nobs_good_idx,   nobs_okay_idx]  = NOBS_list
        [COMP,  COMP_good,   COMP_okay,   comp_pars,   COMP_fit,   comp_good_idx,   comp_okay_idx]  = COMP_list
        [ISIGI, ISIGI_good,  ISIGI_okay,  isigi_pars,  ISIGI_fit,  isigi_good_idx,  isigi_okay_idx] = ISIGI_list

        decision = 'None'
        # GOOD/BAD Ratio, if there too many bad frames it means they need to be laundered through rejectoplot
        # and rerun PRIME
        good, bad = gb_list
        print(good, bad)
        print(bad/(good+bad))
        if 1 - (bad/(good+bad)) > 0.7:
            decision = 'None'
            gb_opinion = 'Good/Bad Opinion is NOMINAL'
        if 1 - (bad/(good+bad)) < 0.7:
            decision = 'rejectoplot'
            gb_opinion = 'Good/Bad Opinion is REJECTOPLOT'
        print('----------------->', decision, gb_opinion) 

        # I**2 should stay 2 and then rise but not above 3
        # If I**2 hovers at 1.5 it means the data is twinned
        # The I**2 fit uses exp3, the offset (c) is the third value retured
        c = i2_pars[2]
        print('c', c)
        if 1.75 < c < 3.0:
            i2_opinion = 'NOMINAL'
        elif 1.75 > c:
            i2_opinion = 'POSSIBLE TWINNING'
        else:
            i2_opinion = 'SOMETHING IS GOING ON WITH I**2'
        print('----------------->', i2_opinion) 

        # Completeness should be at 100 or 99.9
        # The intecept should be 99.95 or higher
        inter = comp_pars[3]
        print('completeness intercept', inter)
        if inter > 99.95:
            comp_opinion = 'NOMINAL' 
        else:
            comp_opinion = 'SOMETHING IS GOING ON WITH COMPLETENESS'
            decision = 'Rerun Prime'

        print('\n\n\n')
        print('        I**2 resolution suggestion: %1.2f (%1.2f)' %(RES[i2_okay_idx],    I2[i2_okay_idx])) 
        print('       CC1/2 resolution suggestion: %1.2f (%1.2f)' %(RES[cc_okay_idx],    CC[cc_okay_idx])) 
        print('Completeness resolution suggestion: %1.2f (%1.2f)' %(RES[comp_okay_idx],  COMP[comp_okay_idx])) 
        print('       N-obs resolution suggestion: %1.2f (%1.2f)' %(RES[nobs_okay_idx],  NOBS[nobs_okay_idx])) 
        print('       IsigI resolution suggestion: %1.2f (%1.2f)' %(RES[isigi_okay_idx], ISIGI[isigi_okay_idx])) 
    
        i2_res = RES[i2_okay_idx]
        cc_res = RES[cc_okay_idx]  
        comp_res = RES[comp_okay_idx]
        nobs_res = RES[nobs_okay_idx]
        isigi_res = RES[isigi_okay_idx]

        res_recom = ((3*cc_res) + (2*i2_res) + comp_res + nobs_res) / 7.0
        print('   RECOMMEND resolution suggestion: %1.2f' %res_recom) 

        if (res_recom - RES[-1]) > 0.02:
            decision = 'Rerun Prime'
        
        decision_dict = {}
        decision_dict['decision'] = decision
        decision_dict['gb_opinion'] = gb_opinion
        decision_dict['i2_opinion'] = i2_opinion
        decision_dict['comp_opinion'] = comp_opinion
        decision_dict['resolution recommendation'] = res_recom
        
        return decision_dict 

    ## real function
    
    prime_dir = data['prime_dir']
    upload_dir = data['upload_dir']

    log_fid = data['prime_input'] 

    os.chdir(upload_dir)

    postref_dict, gb_list = scrape_log_file(log_fid)
    png_fid = 'primalysis.png'
    fitting_list = plot_histograms(postref_dict, gb_list, png_fid)
    decision_dict = decision_engine(fitting_list, gb_list)
    with open('primalysis_decision.json', 'w') as f:
        json.dump(decision_dict, f)

@generate_flow_definition
class Primalisys(GladierBaseTool):
    flow_input = {}
    required_input = [
        'prime_dir',
        'upload_dir',
        'funcx_endpoint_compute',
    ]
    funcx_functions = [
        primalisys
    ]
