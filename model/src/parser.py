from optparse import OptionParser
from arc_hybrid_torch import ArcHybridLSTM
import pickle, utils, os, time, sys
import gc
import torch
import show_output


if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("--train", dest="conll_train", help="Annotated CONLL train file", metavar="FILE", default="../data/PTB_SD_3_3_0/train.conll")
    parser.add_option("--dev", dest="conll_dev", help="Annotated CONLL dev file", metavar="FILE", default="../data/PTB_SD_3_3_0/dev.conll")
    parser.add_option("--test", dest="conll_test", help="Annotated CONLL test file", metavar="FILE", default="./test.conll")
    parser.add_option("--params", dest="params", help="Parameters file", metavar="FILE", default="params.pickle")
    parser.add_option("--extrn", dest="external_embedding", help="External embeddings", metavar="FILE")
    parser.add_option("--model", dest="model", help="Load/Save model file", metavar="FILE", default="barchybrid.model")
    parser.add_option("--wembedding", type="int", dest="wembedding_dims", default=200)
    #parser.add_option("--pembedding", type="int", dest="pembedding_dims", default=25)
    parser.add_option("--pembedding", type="int", dest="pembedding_dims", default=0)
    parser.add_option("--rembedding", type="int", dest="rembedding_dims", default=25)
    parser.add_option("--epochs", type="int", dest="epochs", default=30)
    parser.add_option("--hidden", type="int", dest="hidden_units", default=256)
    parser.add_option("--hidden2", type="int", dest="hidden2_units", default=0)
    parser.add_option("--k", type="int", dest="window", default=3)
    parser.add_option("--lr", type="float", dest="learning_rate", default=0.001)
    parser.add_option("--outdir", type="string", dest="output", default='./outdir')
    parser.add_option("--activation", type="string", dest="activation", default="tanh")
    parser.add_option("--lstmlayers", type="int", dest="lstm_layers", default=2)
    parser.add_option("--lstmdims", type="int", dest="lstm_dims", default=200)
    parser.add_option("--dynet-seed", type="int", dest="seed", default=7)
    parser.add_option("--disableoracle", action="store_false", dest="oracle", default=True)
    parser.add_option("--disableblstm", action="store_false", dest="blstmFlag", default=True)
    parser.add_option("--bibi-lstm", action="store_true", dest="bibiFlag", default=False)
    parser.add_option("--usehead", action="store_true", dest="headFlag", default=False)
    parser.add_option("--userlmost", action="store_true", dest="rlMostFlag", default=False)
    parser.add_option("--userl", action="store_true", dest="rlFlag", default=False)
    parser.add_option("--predict", action="store_true", dest="predictFlag", default=False)
    parser.add_option("--dynet-mem", type="int", dest="cnn_mem", default=512)

    (options, args) = parser.parse_args()
    print 'Using external embedding:', options.external_embedding

    if not options.predictFlag:
        if not (options.rlFlag or options.rlMostFlag or options.headFlag):
            print 'You must use either --userlmost or --userl or --usehead (you can use multiple)'
            sys.exit()

        print 'Preparing vocab'
        #words, w2i, pos, rels = utils.vocab(options.conll_train)
        words, w2i, rels = utils.vocab(options.conll_train)


        with open(os.path.join(options.output, options.params), 'w') as paramsfp:
            #pickle.dump((words, w2i, pos, rels, options), paramsfp)
            pickle.dump((words, w2i, rels, options), paramsfp)
        print 'Finished collecting vocab'
        

        #with open('./output/params.pickle', 'r') as paramsfp:
        #    words, w2i, rels, stored_opt = pickle.load(paramsfp)



        print 'Initializing blstm arc hybrid:'
        #parser = ArcHybridLSTM(words, pos, rels, w2i, options)
        parser = ArcHybridLSTM(words, rels, w2i, options)

        #parser.Load('./output/barchybrid.model3.tmp')


        for epoch in xrange(options.epochs):
            print 'Starting epoch', epoch
            parser.Train(options.conll_train, epoch)
            conllu = (os.path.splitext(options.conll_dev.lower())[1] == '.conllu')
            devpath = os.path.join(options.output, 'dev_coco_1e-2_256_200_' + str(epoch+1) + ('.conll' if not conllu else '.conllu'))
            utils.write_conll(devpath, parser.Predict(options.conll_dev))

            if not conllu:
                os.system('perl src/utils/eval.pl -g ' + options.conll_dev  + ' -s ' + devpath  + ' > ' + devpath + '.txt')
            else:
                os.system('python src/utils/evaluation_script/conll17_ud_eval.py -v -w src/utils/evaluation_script/weights.clas ' + options.conll_dev + ' ' + devpath + ' > ' + devpath + '.txt')
            
            print 'Finished predicting dev'
            parser.Save(os.path.join(options.output, options.model + str(epoch+1)))
    else:
        with open(options.params, 'r') as paramsfp:
            words, w2i, rels, stored_opt = pickle.load(paramsfp)

        stored_opt.external_embedding = options.external_embedding

        parser = ArcHybridLSTM(words, rels, w2i, stored_opt)
        parser.Load(options.model)
        
        
        ############
        with open('./input_sentences.txt', 'r') as f:
            sentences = f.readlines()
            
        with open('./test.conll', 'w') as f:
            for sent in sentences:
                sent = sent.replace('\n', '')
                if sent == '':
                    continue
                    
                if sent.startswith('#'):
                    continue
                words = sent.split(' ')
                for i, word in enumerate(words):
                    f.write('%s\t%s\t_\t_\t_\n' % (str(i+1), word))
                f.write('\n')
        ##############
        
        conllu = (os.path.splitext(options.conll_test.lower())[1] == '.conllu')
        tespath = os.path.join(options.output, 'test_pred.conll' if not conllu else 'test_pred.conllu')
        ts = time.time()
        pred = list(parser.Predict(options.conll_test))
        te = time.time()
        utils.write_conll(tespath, pred)

        if not conllu:
            os.system('perl src/utils/eval.pl -g ' + options.conll_test + ' -s ' + tespath  + ' > ' + tespath + '.txt')
        else:
            os.system('python src/utils/evaluation_script/conll17_ud_eval.py -v -w src/utils/evaluation_script/weights.clas ' + options.conll_test + ' ' + tespath + ' > ' + testpath + '.txt')
        
        #print 'Finished predicting test',te-ts
        show_output.show()

