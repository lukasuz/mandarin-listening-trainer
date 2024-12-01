import numpy as np

class SyllableStats():
    def __init__(self, 
                 syllables, 
                 variants,
                 interactions_path = 'interactions.csv', 
                 date_only='') -> None:
        # 34 (only one 'i' instead of 3, no 'ueng', 'uen' is spelled as 'un', 'uei' as 'ui'), i.e. 4 less than on yoyochinese
        self.finals = ['uang', 'iong', 'iang', 'uan', 'uai', 'ing', 'ian', 'iao', 'eng', 'ong', 'ang', 've', 'ue', 'un', 'ui', 'uo', 'ua', 'in', 'iu', 'ie', 'ia', 'er', 'en', 'ei', 'ou', 'an', 'ao', 'ai', 'v', 'u', 'i', 'e', 'o', 'a'] 
        # 21 + '', y , w
        self.initials = ['sh', 'ch', 'zh', 'w', 'y', 's', 'c', 'z', 'r', 'x', 'q', 'j', 'h', 'k', 'g', 'l', 'n', 't', 'd', 'f', 'm', 'p', 'b', ''] 
        self.finals = self.sort(self.finals)
        self.initials = self.sort(self.initials)
        self.tones = ['1', '2', '3', '4']

        ### Syllables
        self.interactions_path = interactions_path
        self.variants = variants
        self.possible_syllables = np.array(syllables, dtype='U')
        self.parse_sound_files(syllables)
        self.initial_occurences, self.final_occurences, self.tone_occurences, self.syllable_occurences, self.initial_heatmap, self.final_heatmap, self.tone_heatmap, self.unique_days = self.parse_occurences(interactions_path, date_only=date_only)
        self.base_prob = self.get_base_prob(self.possible_syllables)

    def sort(self, arr):
        # Sort by length
        arr = np.array(sorted(list(set(arr)), key=len)[::-1])
        lens = np.array(list(map(len, arr)))
        # Sort alphabetically
        for l in np.unique(lens):
            mask = np.where(l == lens)
            sub_arr = arr[mask]
            sub_arr.sort()
            arr[mask] = sub_arr
        return arr.tolist()

    def get_categories_from_syllable(self, syllable, replace_final_exception=False):
        if syllable == '':
            return '', '', ''
        syllable_wo_num, num = syllable[:-1], syllable[-1:]
        tone = int(num)

        for initial in self.initials:
            if initial == syllable_wo_num[:len(initial)]:
                break
        
        final_found = False
        if initial == '':
            final = syllable_wo_num
            final_found = True
        else:
            for final in self.finals:
                if final == syllable_wo_num[len(initial):]:
                    final_found = True
                    break
        if not final_found:
            if replace_final_exception:
                final = 'XXXXX'
            else:
                raise ValueError('No final found')

        return initial, final, tone

    def parse_sound_files(self, syllables):
        # parse dictionary for all syllables, create mapping from finals and initials to words
        syllable_to_config_idx = {}
        configs = []
        for syllable in syllables:            
            syllable_wo_num, num = syllable[:-1], syllable[-1:]
            num = int(num)
            for initial in self.initials:
                if initial == syllable_wo_num[:len(initial)]:
                    break
            if initial == '':
                final = syllable_wo_num
            else:
                final = syllable_wo_num[len(initial):]

            if syllable not in syllable_to_config_idx.keys(): 
                syllable_to_config_idx[syllable] = len(configs)
                configs.append([self.initials.index(initial), self.finals.index(final), num - 1])

        self.configs = np.array(configs, dtype=int)
        self.syllable_to_config_idx = syllable_to_config_idx

    def get_base_prob(self, syllables):
        initial_occurences = np.zeros((len(self.initials), 2))
        final_occurences = np.zeros((len(self.finals), 2))
        tone_occurences = np.zeros((len(self.tones), 2))
        syllable_occurences = np.zeros((len(self.possible_syllables)))

        initial_heatmap = np.zeros((len(self.initials), len(self.initials), 2))
        final_heatmap = np.zeros((len(self.finals), len(self.finals), 2))
        tone_heatmap = np.zeros((len(self.tones), len(self.tones), 2))
        # For each line, detect config (match word current word of line in dict
        # for each config element we have binary probability
        for syllable in syllables:
            target = answer = syllable
            correct = 1

            self.update_stats(target, answer, correct, initial_occurences, final_occurences, tone_occurences,
                              syllable_occurences, initial_heatmap, final_heatmap, tone_heatmap)
        
        initial_base_prob = initial_occurences[:,1] / initial_occurences[:,1].sum()
        final_base_prob = final_occurences[:,1] / final_occurences[:,1].sum()
        tone_base_prob = tone_occurences[:,1] / tone_occurences[:,1].sum()
        # Sanity check: np.array(self.finals)[np.argsort(final_base_prob)]
        base_prob = initial_base_prob[self.configs[:,0]] * final_base_prob[self.configs[:,1]] * tone_base_prob[self.configs[:,2]]
        # Sanity check: self.possible_syllables[np.argsort(initial_base_prob[self.configs[:,0]] * final_base_prob[self.configs[:,1]] * tone_base_prob[self.configs[:,2]])][:20]
        return base_prob

    def parse_occurences(self, interactions_path, skip_empty_answer=False, date_only=''):
        initial_occurences = np.zeros((len(self.initials), 2))
        final_occurences = np.zeros((len(self.finals), 2))
        tone_occurences = np.zeros((len(self.tones), 2))
        syllable_occurences = np.zeros((len(self.possible_syllables)))

        initial_heatmap = np.zeros((len(self.initials), len(self.initials), 2))
        final_heatmap = np.zeros((len(self.finals), len(self.finals), 2))
        tone_heatmap = np.zeros((len(self.tones), len(self.tones), 2))

        unique_day = []

        # For each line, detect config (match word current word of line in dict
        # for each config element we have binary probability
        with open(interactions_path, 'r') as f:
            lines = f.readlines()
        lines = lines[1:]
        for line in lines:
            target, answer, correct, date, _, _ = line.split(',')
            day = date.split(' ')[0]
            if day not in unique_day:
                unique_day.append(day)

            correct = int(correct)
            if date_only != '':
                if date_only not in date:
                    continue

            if answer == '' and skip_empty_answer:
                continue

            self.update_stats(target, answer, correct, initial_occurences, final_occurences, tone_occurences,
                              syllable_occurences, initial_heatmap, final_heatmap, tone_heatmap)

        return initial_occurences, final_occurences, tone_occurences, syllable_occurences, initial_heatmap, final_heatmap, tone_heatmap, unique_day
    
    def update_stats(self, target, answer, correct, initial_occurences=None, final_occurences=None, tone_occurences=None, syllable_occurences=None, initial_heatmap=None, final_heatmap=None, tone_heatmap=None):
        if initial_occurences is None or final_occurences is None or tone_occurences is None or syllable_occurences is None:
            initial_occurences = self.initial_occurences
            final_occurences = self.final_occurences
            tone_occurences = self.tone_occurences
            syllable_occurences = self.syllable_occurences

        if initial_heatmap is None or final_heatmap is None or tone_heatmap is None:
            initial_heatmap = self.initial_heatmap
            final_heatmap = self.final_heatmap
            tone_heatmap = self.tone_heatmap

        if target not in self.syllable_to_config_idx:
            return
    
        syllable_occurences[np.where(np.array(target, dtype='U') == self.possible_syllables)] += 1
        if not correct == 2 and not 'give up' in answer and answer != '':  #NOTE: 2 means give up, currently mapping to uncorrect manually
            initial_t, final_t, tone_t = self.get_categories_from_syllable(target)
            initial_a, final_a, tone_a = self.get_categories_from_syllable(answer, replace_final_exception=True)

            initial_c = int(initial_a == initial_t)
            final_c = int(final_a == final_t)
            tone_c = int(tone_a == tone_t)

            if initial_a in self.initials:
                initial_heatmap[self.initials.index(initial_a), self.initials.index(initial_t), initial_c] += 1
                # initial_heatmap[self.initials.index(initial_t), self.initials.index(initial_a)] += 1-initial_c

            if final_a in self.finals:
                final_heatmap[self.finals.index(final_a), self.finals.index(final_t), final_c] += 1
                # final_heatmap[self.finals.index(final_t), self.finals.index(final_a)] += 1-final_c
                
            if str(tone_a) in self.tones:
                tone_heatmap[tone_a-1, tone_t-1, tone_c] += 1
                # tone_heatmap[tone_t-1, tone_a-1] += 1-tone_c

        else:
            initial_c = 0
            final_c = 0
            tone_c = 0

        inital_num, final_num, tone_num = self.configs[self.syllable_to_config_idx[target]]
        initial_occurences[inital_num, initial_c] += 1
        final_occurences[final_num, final_c] += 1
        tone_occurences[tone_num, tone_c] += 1

    def get_recall_prob(self, x, eps=1e-8):
        abs = x.sum(axis=-1, keepdims=True)
        pos_abs = x[:,1]
        return (x / (abs + eps))[:,1], abs[:,0].astype(int), pos_abs.astype(int)

    def get_syllable_sampling_prob(self, c_low=0.01, c_high=0.99, exp=True, non_sampled_boost=False):
        # Calculate the guessing right probability for each category
        initial_correct_prob, _, _ = self.get_recall_prob(self.initial_occurences)
        final_correct_prob, _, _ = self.get_recall_prob(self.final_occurences)
        tone_correct_prob, _, _ = self.get_recall_prob(self.tone_occurences)

        initial_correct_prob = np.clip(initial_correct_prob, c_low, c_high)
        final_correct_prob = np.clip(final_correct_prob, c_low, c_high)
        tone_correct_prob = np.clip(tone_correct_prob, c_low, c_high)

        syllable_prob = self.base_prob * initial_correct_prob[self.configs[:,0]] * final_correct_prob[self.configs[:,1]] * tone_correct_prob[self.configs[:,2]]
        sampling_prob = 1 - syllable_prob
        if exp:
            sampling_prob = np.expm1(sampling_prob)
        if non_sampled_boost > 0:
            sampling_prob = sampling_prob + non_sampled_boost * sampling_prob.mean() * np.array(self.syllable_occurences == 0, dtype=int)
        # print(np.array(self.syllable_occurences == 0, dtype=int).sum(), np.array(self.syllable_occurences).sum())
        sampling_prob = sampling_prob / sampling_prob.sum()
        return sampling_prob

    def get_rnd_syllable(self, num=1, advanced=False, non_sampled_boost=False):
        p = self.get_syllable_sampling_prob(non_sampled_boost=non_sampled_boost)
        syllables = self.possible_syllables
        if advanced: # Restrict to 'worst' 100 or num*2 samples   
            mask = p.argsort()[::-1][:max(num*2, 100)]
            p = p[mask]
            p = p / p.sum()
            syllables = syllables[mask]
        # TODO: keep track of last sample, do not use again for next sample
        return list(np.random.choice(syllables, (num,), replace=False, p=p)), list(np.random.choice(self.variants, (num,), replace=True))
    
    def plot(self, w=18, h=9.5):
        import seaborn as sns
        import matplotlib.pyplot as plt
        import matplotlib.gridspec as gridspec
        import scipy.stats as sc_stats

        sns.set_theme(style="whitegrid")

        def plot_barplot(occurences, confidence_level = 0.95, title='', xticks=None):
            correct_prob, abs, pos_abs = self.get_recall_prob(occurences)

            errors_lower = []
            errors_upper = []
            for i in range(len(pos_abs)):
                if abs[i] == 0:
                    errors_lower.append(correct_prob[i])
                    errors_upper.append(correct_prob[i])
                    continue
                test = sc_stats.binomtest(pos_abs[i], abs[i], p=0.5, alternative='two-sided')
                ci = test.proportion_ci(confidence_level=confidence_level, method='exact')
                errors_lower.append(ci.low)
                errors_upper.append(ci.high)
            errors_lower = correct_prob - np.array(errors_lower)
            errors_upper = np.array(errors_upper) - correct_prob

            xs = np.arange(len(correct_prob))
            ax = sns.barplot(x=xs, y=correct_prob, palette=sns.color_palette("husl", len(xs)))
            ax.errorbar(x=xs, y=correct_prob, 
                        yerr=[errors_lower, errors_upper], fmt='none', 
                        c='black', capsize=3)
            # sns.lineplot(x=[xs[0]-1, xs[-1]+1], y=2*[correct_prob.mean()])

            mean = correct_prob[abs > 0].mean()
            # plt.text(xs[0]-0.5, mean, 'μ', ha='left', va='bottom', color='black', alpha=0.8)
            plt.plot([xs[0]-0.5, xs[-1]+0.5], 2*[mean], color='red', linestyle='dashed', linewidth=1.5, alpha=0.5)
            
            ax.set_xticklabels(xticks, rotation='vertical')
            ax.set_yticks(np.linspace(0,1,11))
            xticks = ax.get_xticklabels()
            for i, tick in enumerate(xticks):
                if abs[i] == 0:
                    col = 'red'
                else:
                    col = 'black'
                tick.set_color(col)

            ax.set_title(title)
            ax.set_ylabel('P(Guess) = 1')

        def plot_heatmap(heatmap, ticks, title=''):
            # heatmap
            # heatmap[0,:] += 200 # y, x
            # heatmap = heatmap[:,:,0] / (heatmap[:,:,1].sum(axis=0, keepdims=True) + 1e-8)
            heatmap = heatmap[:,:,0] / (heatmap.sum(axis=0, keepdims=True).sum(axis=-1) + 1e-8)
            ax = sns.heatmap(heatmap, cmap='mako_r')
            ax.set(xlabel='Heard', ylabel='Typed')
            plt.xticks(ticks=np.arange(len(heatmap))+0.5, labels=ticks, rotation='vertical')
            plt.yticks(ticks=np.arange(len(heatmap))+0.5, labels=ticks, rotation='horizontal')

            for i in range(len(heatmap)):
                plt.plot([0, len(heatmap)], 2*[i+0.5], color='black', linestyle='dashed', linewidth=1, alpha=0.2)
                plt.plot(2*[i+0.5], [0, len(heatmap)], color='black', linestyle='dashed', linewidth=1, alpha=0.2)
            # ax.xaxis.tick_top()
            plt.title(title)

        def plot_over_time(names, interactions_path, unique_dates, parse_occurences):
            occurences_per_date = []
            for date in unique_dates:
                occurences_per_date.append(parse_occurences(interactions_path, date_only=date))

            probs = np.zeros((len(unique_dates), len(names)))
            for d in range(len(unique_dates)):
                for n in range(len(names)):
                    correct_prob, abs, _ = self.get_recall_prob(occurences_per_date[d][n])
                    probs[d,n] = correct_prob[abs > 0].mean()
            
            cols = sns.color_palette("husl", 3)
            x = np.arange(len(unique_dates))
            sns.lineplot(y=probs[:,0], x=x, label=names[0], color=cols[0])
            sns.lineplot(y=probs[:,1], x=x, label=names[1], color=cols[1])
            sns.lineplot(y=probs[:,2], x=x, label=names[2], color=cols[2])
            plt.title('Average Guessing Probability over Time')
            plt.ylabel('P(Guess) = 1')
            labels = list(len(x) * [''])
            labels[0] = unique_dates[0]
            labels[-1] = unique_dates[-1]
            if len(x) % 2 == 0:
                s1 = len(x) // 4
                s2 = 2 * s1
                labels[s1] = unique_dates[s1]
                labels[s2] = unique_dates[s2]
            else:
                mid = len(x) // 2
                labels[mid] = unique_dates[mid]
            plt.xticks(x, labels=labels, rotation=20)
            plt.legend()
        
        ### Syllables
        plt.figure(figsize=(w, h))
        gs = gridspec.GridSpec(6, 3, width_ratios=[1, 1, h/w])
        
        plt.subplot(gs[:3, 0])
        plot_heatmap(self.initial_heatmap, self.initials, title='Confusion Matrix Initials')
        plt.subplot(gs[:3, 1])
        plot_heatmap(self.final_heatmap, self.finals, title='Confusion Matrix Finals')
        plt.subplot(gs[:2, 2])
        plot_heatmap(self.tone_heatmap, self.tones, title='Confusion Matrix Tones')

        plt.subplot(gs[3:, 0])
        plot_barplot(self.initial_occurences, title='Initials Guessing Probability', xticks=self.initials)
        plt.subplot(gs[3:, 1])
        plot_barplot(self.final_occurences, title='Finals Guessing Probability', xticks=self.finals)
        plt.subplot(gs[2:4, 2])
        plot_barplot(self.tone_occurences, title='Tone Guessing Probability', xticks=self.tones)

        plt.subplot(gs[4:6, 2])
        plot_over_time(['Initials', 'Finals', 'Tones'], self.interactions_path, self.unique_days, self.parse_occurences)

        plt.tight_layout()
        plt.show()

def plot():
    from data import SYLLABLES, VARIANTS
    stats = SyllableStats(syllables=SYLLABLES, variants=VARIANTS, date_only='')
    stats.plot()

if __name__ == '__main__':
    plot()