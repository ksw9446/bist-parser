with open('input_sentences.txt', 'r') as f:
    sentences = f.readlines()
    
with open('test.conll', 'w') as f:
    for sent in sentences:
        sent = sent.replace('\n', '')
        if sent == '':
            continue
        words = sent.split(' ')
        for i, word in enumerate(words):
            f.write('%s\t%s\t_\t_\t_\n' % (str(i+1), word))
        f.write('\n')
        
