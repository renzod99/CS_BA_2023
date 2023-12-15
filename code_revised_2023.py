from bootstrap import *
from bootstrap import bootStrap
import json
from TV_class import TVObjectsFromJson
import time
import matplotlib.pyplot as plt
##########################################################################
def format_json_file(file_path):
    with open(file_path, 'r') as file:
        dad = json.load(file)
    tv_list = TVObjectsFromJson(dad)
    return tv_list

tv_list = format_json_file('TVs-all-merged.json')

#########################################################################################################################################################
print("start")
overall_start = time.time()

num_hash = 400
num_bags = 5
bootstrap_dict, bootstrap_dup_dict = bootStrap(tv_list,num_bags, False)
bootstrap_dict = sizeMwCatBoot(bootstrap_dict)
bootstrap_dict = resMwCatBoot(bootstrap_dict)
bootstrap_dict = refMwCatBoot(bootstrap_dict)

tp_fp_LSH, metrics_LSH, tp_fp_clustering, metrics_clustering = LSHandClus(bootstrap_dict, bootstrap_dup_dict ,num_hash)


a = bootstrap_dict[0][0]
b = bootstrap_dict[0][1]
# #############################################################################
print("start: plotting")
start = time.time()

def prepPlot(metrics_list):
    sums_and_counts = defaultdict(lambda: [0, 0, 0, 0, 0])
    for PQ_s, PC_s, F1_s, fc_LSH, i, b, r in metrics_list:
        sums_and_counts[(b, r)][0] += PQ_s
        sums_and_counts[(b, r)][1] += PC_s
        sums_and_counts[(b, r)][2] += F1_s
        sums_and_counts[(b, r)][3] += fc_LSH
        sums_and_counts[(b, r)][4] += 1  # Count
    
    averages = {}
    for key, (sum_PQ_s, sum_PC_s, sum_F1_s, sum_fc_LSH, count) in sums_and_counts.items():
        averages[key] = (
            sum_PQ_s / count,
            sum_PC_s / count,
            sum_F1_s / count,
            sum_fc_LSH / count)
    return averages

def prepPlot2(metrics_list):
    sums_and_counts = defaultdict(lambda: [0, 0, 0])
    for tp, fp, i, b, r in metrics_list:
        sums_and_counts[(b, r)][0] += tp
        sums_and_counts[(b, r)][1] += fp
        sums_and_counts[(b, r)][2] += 1  # Count
    
    averages = {}
    for key, (tp_sum, fp_sum, count) in sums_and_counts.items():
        averages[key] = (
            tp_sum / count,
            fp_sum / count,)
    return averages

LSH_averages = prepPlot(metrics_LSH)
clustering_averages = prepPlot(metrics_clustering)
LSH_tpfp = prepPlot2(tp_fp_LSH)
clustering_tpfp = prepPlot2(tp_fp_clustering)

# ### Plotting LSH -->
# Extract the averages from the averages dictionary
PQ_LSH = [avg[0] for avg in LSH_averages.values()]
PC_LSH = [avg[1] for avg in LSH_averages.values()]
F1_s = [avg[2] for avg in LSH_averages.values()]
foc = [avg[3] for avg in LSH_averages.values()]
tp_LSH = [tup[0] for tup in LSH_tpfp.values()]
fp_LSH = [tup[1] for tup in LSH_tpfp.values()]

# ### Plotting clustering -->
PQ = [avg[0] for avg in clustering_averages.values()]
PC = [avg[1] for avg in clustering_averages.values()]
F1 = [avg[2] for avg in clustering_averages.values()]
focc = [avg[3] for avg in clustering_averages.values()]
tp_clustering = [tup[0] for tup in clustering_tpfp.values()]
fp_clustering = [tup[1] for tup in clustering_tpfp.values()]

plt.figure(figsize=(10, 6))
plt.plot(foc, PC_LSH, label='Pair Completeness_LSH', marker='^')
plt.plot(focc, PC, label='Pair Completeness_clus', marker='o')
plt.xlim(0,0.4)
plt.xlabel('Fraction of Comparisons')
plt.ylabel('Pair Completeness')
plt.title('PC vs FoC')
plt.legend()
plt.grid(True)
plt.show()

plt.figure(figsize=(10, 6))
plt.plot(foc, PQ_LSH, label='Pair Quality_LSH', marker='1')
plt.plot(foc, F1_s, label='F1*', marker='2')
plt.xlim(0,0.4)
plt.ylim(0, 0.15)
plt.xlabel('Fraction of Comparisons')
plt.ylabel('F1* and PQ')
plt.title(f'F1* and PQ vs FoC, #hashfuncs = {num_hash}')
plt.legend()
plt.grid(True)
plt.show()

plt.figure(figsize=(10, 6))
plt.plot(focc, PQ, label='Pair Quality_clus', marker='3')
plt.plot(focc, F1, label='F1', marker='4')
plt.xlim(0.075,0.15)
plt.ylim(0, 0.8)
plt.xlabel('Fraction of Comparisons')
plt.ylabel('F1 and PQ')
plt.title(f'F1 and PQ vs FoC, #hashfuncs = {num_hash}')
plt.legend()
plt.grid(True)
plt.show()

# plt.figure(figsize=(10, 6))
# plt.plot(foc, tp_LSH, label='#TP_LSH', marker='p')
# plt.plot(foc, fp_LSH, label='#FP_LSH', marker='s')
# plt.plot(focc, tp_clustering, label='#TP', marker='o')
# plt.plot(focc, fp_clustering, label='#FP', marker='^')
# plt.xlabel('Fraction of Comparisons')
# plt.ylabel('#TP, #FP')
# plt.title('#TP, #FP vs FoC')
# plt.legend()
# plt.grid(True)
# plt.show()

end = time.time()
print(f"Time taken: {end - start} seconds")
overall_end = time.time()
print(f" Overall Time taken: {overall_end - overall_start} seconds")


