import sys
import time
import random
import numpy as np
from collections import Counter
from timeit import default_timer as timer
import multiprocessing

class Node(object):
    def __init__(self, feature, value, left=None, right=None, _class=None):
        self.feature = feature
        self.value = value
        self.left = left
        self.right = right
        self._class = _class

    def __repr__(self):
        node_repr = "Node(f_index:{} - value:{} - class:{})"
        reprs = node_repr.format(str(self.feature),
                         str(self.value),
                         str(self._class))
        return reprs

def split(dataset, f_index, value):
    left = {"X":[], "Y": []}
    right = {"X": [], "Y": []}
    X = dataset["X"]
    Y = dataset["Y"]
    
    for x,y in zip(X,Y):
        if x[f_index] <= value:
            left["X"].append(x)
            left["Y"].append(y)
            
        else:
            right["X"].append(x)
            right["Y"].append(y)
    groups = {'left':left, 'right':right}
    return groups

def get_entropy_of_split(dataset, f_index, value, classes):
    groups_dict = split(dataset, f_index, value)
    groups = []
    groups.append(groups_dict['left'])
    groups.append(groups_dict['right'])

    entropy = 0
    total_size = len(dataset['Y'])
    
    for group in groups:
        class_count = Counter(group['Y'])
        length_group = float(len(group["X"]))
        normal_size = float(length_group)/total_size
        group_entropy = 0
    
        for _class in classes:
            if not class_count.has_key(_class):
                continue
            count = class_count[_class]
            prob = float(count)/length_group
            group_entropy -= prob*np.log2(prob)
        entropy += normal_size*group_entropy
    return entropy, groups_dict

def cal_gain(dataset, classes, f_index, value):

    classes_count = Counter(dataset['Y'])
    total_count = len(dataset['Y'])
    initial_entropy = 0

    for _class in classes:
        prob = float(classes_count[_class])/total_count
        initial_entropy -= prob*np.log2(prob)

    entropy_of_split, groups = get_entropy_of_split(dataset, f_index, value, classes)
    gain = initial_entropy-entropy_of_split
    return gain, groups


def majority_voting(dataset):
    Y = dataset['Y']
    Y_count = Counter(Y)
    _class = max(Y_count)
    return _class

def construct(dataset, limits, classes, features, roots, i, randomtree=False):
    if not randomtree:
        root = construct_decision_tree(dataset, limits, classes, features, 0)
        roots[i] = root
    else:
        root = construct_decision_tree(dataset, limits, classes, features, 0, randomtree=True)
        roots[i] = root

def construct_decision_tree(dataset, limits, classes, features, depth, randomtree=False):
    #Stop when depth is reached
    if depth_limit:
        if depth == depth_limit:
            _class = majority_voting(dataset)
            return Node(None,
                        None,
                        _class=_class)
        
    #Stop when no samples left
    if not dataset['X']:
        return None
        
    #Stop when all belong to same class                
    if len(classes) == 1:
        return Node(None,
                    None,
                    _class=classes[0])

    #Stop when no features are left
    if not features:
        _class = majority_voting(dataset)
        return Node(None,
                    None,
                    _class=_class)

    X = dataset['X']
    Y = dataset['Y']

    _gains = []
    for f_index in features:
        information_gain = []
        _min = limits[f_index]['min']
        _max = limits[f_index]['max']
        for value in np.linspace(_min, _max, 5):
            gain, groups = cal_gain(dataset, classes, f_index, value)
            information_gain.append({'value':value,
                                     'gain': gain,
                                     'groups':groups})
            
        max_gain_pair = max(information_gain, key=lambda i:i['gain'])
        _gains.append({'f_index':f_index,
                       'max_gain':max_gain_pair['gain'],
                       'value':max_gain_pair['value'],
                       'groups':max_gain_pair['groups']})

    if not randomtree:
        selected = max(_gains, key=lambda i:i['max_gain'])

    else:
        sorted(_gains, key=lambda i:i['max_gain'])
        top_length = int(np.sqrt(len(features)))
        selected = _gains[random.randint(0, top_length)]
        
    node = Node(selected['f_index'],
                selected['value'],
                _class=None)        

    new_features = []
    for f_index in features:
        if f_index != selected['f_index']:
            new_features.append(f_index)

    left_data = selected['groups']['left']
    left_limits = get_limits(left_data, new_features)
    left_classes = get_classes(left_data)
    
    right_data = selected['groups']['right']
    right_limits = get_limits(right_data, new_features)
    right_classes = get_classes(right_data)
    
    node.left =  construct_decision_tree(left_data,
                                         left_limits,
                                         left_classes,
                                         new_features,
                                         depth+1)

    node.right = construct_decision_tree(right_data,
                                         right_limits,
                                         right_classes,
                                         new_features,
                                         depth+1)
    return node

def get_limits(dataset, features):
    X = dataset['X']
    limits = {}
    for index in features:
        limits[index] = {'min':None, 'max':None}

    for x in X:
        for index in features:
            if limits[index]['min'] == None:
                limits[index]['min'] = x[index]
            elif x[index] < limits[index]['min']:
                limits[index]['min'] = x[index]
                
            if limits[index]['max'] == None:
                limits[index]['max'] = x[index]
            elif x[index] > limits[index]['max']:
                limits[index]['max'] = x[index]
    return limits

def get_classes(dataset):
    Y = dataset['Y']
    return list(set(Y))

nodes = {}
edges = []

def get_nodes(node, i):
    if not node:
        return
    nodes[i] = str(node)
    get_nodes(node.left, 2*i+1)
    get_nodes(node.right, 2*i+2)

def get_edges(node, i):
    global nodes, edges
    for key, value in nodes.items():
        if nodes.has_key(2*key+1):
            edges.append([key, 2*key+1])
        if nodes.has_key(2*key+2):
            edges.append([key, 2*key+2])

def get_nodes_edges(node, filename):
    i = 0
    get_nodes(node, i)
    get_edges(node, i)
    nodes_fp = open('nodes-{}.csv'.format(filename), 'a')
    edges_fp = open('edges-{}.csv'.format(filename), 'a')

    for key, value in nodes.items():
        nodes_fp.write(str(key)+','+value+'\n')

    for edge in edges:
        edges_fp.write(str(edge[0])+','+str(edge[1])+',Undirected'+',1\n')

    nodes_fp.close()
    edges_fp.close()
        
        
def classify(root, X_data):
    classified = []
    for x in X_data:
        node = root
        while(node != None):
            if node._class != None:
                classified.append(node._class)
                break
            else:
                if x[node.feature] <= node.value:
                    node = node.left
                else:
                    node = node.right
    return classified

def extract_data(data, ratio, sepr):
    split_len = len(data)*ratio/100
    training_set = []
    X_train = []
    Y_train = []
    X_test = []
    Y_test = []
        
    while(len(training_set) < split_len):
        index = random.randint(0, len(data)-1)
        training_set.append(data.pop(index))

    for vector in training_set:
        if sepr == 2:
            vector = map(str.strip, vector.split(','))
        else:
            vector = map(str.strip, vector.split())
        try:
            Y_train.append(int(vector.pop(-1)))
            X_train.append(map(float, vector))
        except:
            print "Error occured while reading data(Ensure proper format).. "
            return

    for vector in data:
        if sepr == 2:
            vector = map(str.strip, vector.split(','))
        else:
            vector = map(str.strip, vector.split())
        Y_test.append(int(vector.pop(-1)))
        X_test.append(map(float, vector))

    return X_train, Y_train, X_test, Y_test

def bagging_split(dataset, K, overlap=0):
    X_train = dataset['X']
    Y_train = dataset['Y']
    
    split_len = len(X_train)/K
    bagging_data_X = []
    bagging_data_Y = []

    for i in range(K):
        row_data_X = []
        row_data_Y = []
        while(len(row_data_X) < split_len):
            index = random.randint(0, len(X_train)-1)
            row_data_X.append(X_train.pop(index))
            row_data_Y.append(Y_train.pop(index))
        bagging_data_X.append(row_data_X)
        bagging_data_Y.append(row_data_Y)

    overlap_length = int(split_len*overlap/100.0)
    overlap_data_X = [[] for i in xrange(K)]
    overlap_data_Y = [[] for i in xrange(K)]
    
    for i in xrange(K):
        all_sets = range(K)
        all_sets.remove(i)

        for _ in xrange(overlap_length):
            set_index = random.sample(all_sets, 1)[0]
            len_set = len(bagging_data_X[set_index])
            data_index = random.randint(0, len_set-1)

            overlap_data_X[i].append(bagging_data_X[set_index][data_index])
            overlap_data_Y[i].append(bagging_data_Y[set_index][data_index])

    for i in xrange(K):
        bagging_data_X[i].extend(overlap_data_X[i])
        bagging_data_Y[i].extend(overlap_data_Y[i])

    return bagging_data_X, bagging_data_Y

def bagging(dataset, K, randomTree=False):
    X = dataset['X']
    Y = dataset['Y']
    
    manager = multiprocessing.Manager()
    roots_dict = manager.dict()
    jobs = []
    
    for i in xrange(K):
        dataset = {'X':X[i], 'Y':Y[i]}
        p = multiprocessing.Process(target=construct, args=(dataset,limits,classes,
                                                            features,roots_dict,i,
                                                            randomTree))
        jobs.append(p)
        p.start()

    for proc in jobs:
        proc.join()

    return roots_dict.values()

def accuracy(pred, actual):
    acc = 0.0
    for y_, y in zip(pred, actual):
        if y_ == y:
           acc += 1
    return acc/len(pred)

def bagg_classify(roots, test_data):
    bagg_pred = []
    predictions = []
    for root in roots:
        bagg_pred.append(classify(root, test_data))

    _pred = [[] for i in range(len(roots))]
    for i in range(len(bagg_pred)):
        for j in range(len(bagg_pred[0])):
            _pred[i].append(bagg_pred[i][j])
    bagg_pred = np.ndarray.tolist(np.transpose(np.array(bagg_pred)))

    for i in bagg_pred:
        predictions.append(max(Counter(i)))
    return predictions

    
depth_limit = 0

if __name__ == "__main__":
    start = timer()
    global depth_limit
    filename = raw_input("Enter the file name: ")
    seperated = int(raw_input("Type of file\n1.Space seperated\n2.Comma seperated\noption: "))
    split_ratio = int(raw_input("Enter the train/test split ratio: "))
    d = int(raw_input("Enter the depth(0 for no limit): "))
    if d != 0:
        depth_limit = d
    
    option = int(raw_input("Choose from below\n1.Basic Decision\n2.Bagging\n3.Random Forest\noption: "))

    with open(filename, 'r') as fp:
        data = fp.readlines()
    X_train, Y_train, X_test, Y_test = extract_data(data, 90, seperated)

    features = range(len(X_train[0]))
    dataset = {'X':X_train, 'Y':Y_train}
    classes = get_classes(dataset)
    limits = get_limits(dataset, features)
    
    if option == 1:
        print "Training a basic Decision tree... "
        root = construct_decision_tree(dataset, limits, classes, features, 0)
        Y_ = classify(root, X_test)
        accu = accuracy(Y_, Y_test)
        print "Accuracy: {}".format(accu)

    elif option == 2:
        K = int(raw_input("Enter K: "))
        overlap = int(raw_input("Enter the percent of overlap: "))
        print "Training {} trees with {} overlap...".format(K, overlap)
        
        X, Y = bagging_split(dataset, K, overlap)
        bagg_dataset = {'X':X, 'Y':Y}
        roots = bagging(bagg_dataset, K)
        Y_ = bagg_classify(roots, X_test)
        accu = accuracy(Y_, Y_test)
        print 'Accuracy: {}'.format(accu)

    elif option == 3:
        K = int(raw_input("Enter K: "))
        overlap = int(raw_input("Enter the percent of overlap: "))
        print "Training {} random forests with {} overlap...".format(K, overlap)
    
        X, Y = bagging_split(dataset, K, overlap)
        bagg_dataset = {'X':X, 'Y':Y}
        roots = bagging(bagg_dataset, K, randomTree=True )
        Y_ = bagg_classify(roots, X_test)
        accu = accuracy(Y_, Y_test)
        print 'Accuracy: {}'.format(accu)
        
    print '\nTime taken: {}\n'.format(timer() - start)
    option2 = int(raw_input("Do you want to test classify the data?\n1.Yes\n2.No\noption: "))
    if option2 == 1:
        _input = map(float, raw_input("Enter the features (space seperated): ").split())
        print _input
        if option == 1:
            print "Classification: {}".format(classify(root, [_input])[0])
        else:
            print "Classification: {}".format(bagg_classify(roots, [_input])[0])
