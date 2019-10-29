import graphviz as gv
from matplotlib import pyplot as plt
import sys

def show():
    target_path = './outdir/test_pred.conll' #sys.argv[1]

    with open(target_path, 'r') as f:
        output_lines = f.readlines()

    output_dataset = []
    words = []
    print ''
    print '--------- output ----------'
    for line in output_lines:
        if line == '\n':
            sentence = ' '.join([word['word'] for word in words])
            output_dataset.append({'sentence':sentence, 'words':words})
            words = []
            print('')
            continue
        elements = line.replace('\n','').split('\t')
        print(elements)
        word = {
            'id':elements[0],
            'word':elements[1],
            'parents':elements[2],
            'type':elements[3]
        }
        words.append(word)
        
    for i, sentence in enumerate(output_dataset):
        sg = gv.Digraph('structs', format='png')
        sg.attr(label='"'+sentence['sentence']+'"', rankdir='LR', fontsize='20')
        # draw node
        colors = {
            'ATTR':'palegreen',
            '_':'white',
            'OBJT':'skyblue',
            'PRED':'salmon',
            'same':'skyblue',
        }
        shape = 'ellipse' if word['type'] == 'PRED' else 'box'
        for word in sentence['words']:
            if word['parents'] == '-1' or word['parents'] == '_':
                continue
            color = colors[word['type']]
            pencolor = 'red' if word['parents'] == '0' else 'black'
            penwidth = '2' if word['parents'] == '0' else '1'
            sg.node(word['id'], label=word['word'], shape=shape, style='filled', fillcolor=color, fontsize='20',
                    penwidth=penwidth, color=pencolor)
            
        # draw edge
        for word in sentence['words']:
            if word['parents'] == '-1' or word['parents'] == '0' or word['parents'] == '_':
                continue
            sg.edge(word['id'], word['parents'], label=word['type'], fontsize='16')
            
        sg.render('./graph%d'%i, view=True, cleanup=True)
        #sg.view()
        
if __name__ == '__main__':
    show()
