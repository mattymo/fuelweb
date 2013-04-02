#!/usr/bin/env python
import random

class NetChecker(object):
    def __init__(self, nodes, arcs):
        self.nodes = nodes
        self.arcs = self._drop_unidir_ifaces(arcs)

    @staticmethod
    def _invert_arc(arc):
        return arc[1], arc[0]

    @staticmethod
    def _create_arc(a_vertex, b_vertex):
        return a_vertex, b_vertex

    @staticmethod
    def _disassm_vertex(vertex):
        index = vertex.find('.')
        node = vertex[:index]
        interface = vertex[index + 1:]
        return node, interface

    @staticmethod
    def _assm_vertex(node, interface):
        return "%s.%s" % (str(node), str(interface))

    @classmethod
    def _drop_unidir_ifaces(klass, arcs):
        newarcs = []
        while arcs:
            arc = arcs.pop()
            inv_arc = klass._invert_arc(arc)
            try:
                arcs.remove(inv_arc)
                newarcs.append(arc)
            except ValueError:
                pass
        return newarcs

    def get_choices(self):
        """ Main method to collect all possible altermatives of
        interconnection.
        """
        choices = []
        vertices = set([i[0] for i in self.arcs])
        while vertices:
            vertex = vertices.pop()
            print "Entry vertex is: ", vertex
            good_topos, visited_vertices = self._calc_topo(vertex)
            choices.extend(good_topos)
            vertices.difference_update(visited_vertices)

        return choices

    def _calc_topo(self, start_vertex):
        topos = []
        visited_vertices = set()

        def extend_arcs_to_check(arcs_to_check, arcs):
            for failed_v, ignored_v in arcs:
                existed_arcs = filter(
                    lambda x: x[0] == failed_v, arcs_to_check)
                if existed_arcs:
                    existed_arc = existed_arcs[0]
                    existed_arc[1].append(ignored_v)
                else:
                    arcs_to_check.append((failed_v, [ignored_v]))

        # arcs_to_check consists of arcs (x, y) where
        # x - failed vertex,
        # y - list of vertices which should be ignored.
        arcs_to_check = [(start_vertex, [])]
        for fv, ignored_vertices in arcs_to_check:
            found_vertices = [fv]
            failed_arcs = []

            for vertex in found_vertices:
                neighbours = self._get_neighbours(vertex)
                new_vertices, absent_vertices = self._diff_lists(
                    found_vertices, ignored_vertices, neighbours
                )
                print new_vertices
                print absent_vertices
                print ' - - - '
                if absent_vertices:
                    for v in absent_vertices:
                        failed_arc = (v, vertex)
                        if failed_arc not in failed_arcs:
                            failed_arcs.append(failed_arc)
                found_vertices.extend(new_vertices)

            failed_vertices = [x[0] for x in failed_arcs]
            topo = self._validate_topo(found_vertices, failed_vertices)
            visited_vertices.update(found_vertices)
            visited_vertices.update(failed_vertices)
            if topo:
                topos.append(topo)
            extend_arcs_to_check(arcs_to_check, failed_arcs)
        return topos, visited_vertices

    def _get_neighbours(self, vertex):
        arcs = filter(
            lambda x: x[0] == vertex,
            self.arcs)
        return [x[0] for x in arcs]

    @staticmethod
    def _diff_lists(found_vertices, ignored_vertices, neighbours):
        # print found_vertices
        # print ignored_vertices
        # print neighbours
        # print "    ------"
        new_vertices = []
        absent_vertices = []
        for n in found_vertices:
            # print "n: ", n
            if n in neighbours:
                neighbours.remove(n)
            else:
                absent_vertices.append(n)
        new_vertices = [n for n in neighbours if n not in ignored_vertices]
        return new_vertices, absent_vertices

    def _validate_topo(self, found_v, failed_v):
        topo = {}
        for v in found_v:
            if v in failed_v:
                continue
            node, interface = self._disassm_vertex(v)
            interfaces = topo.get(node)
            if interfaces:
                interfaces.append(interface)
            else:
                topo[node] = [interface]
        if self.nodes != topo.keys():
            return None
        for l in topo.values():
            l.sort()
        return topo





def getArcs(nodes, interfaces, stability=1.0):
    A = []
    for n1 in nodes:
        for i1 in interfaces:
            for n2 in nodes:
                for i2 in interfaces:
                    # Drop some arcs if stability < 1.0
                    if stability == 1.0 or random.random() < stability:
                        a_vertex = NetChecker._assm_vertex(n1, i1)
                        b_vertex = NetChecker._assm_vertex(n2, i2)
                        arc = NetChecker._create_arc(a_vertex, b_vertex)
                        A.append(arc)
    return A

def printChoice(choice, step=4):
    def printlist(l, indent=0, step=2):
        print '%s[' % (' ' * indent)        
        for i in l:
            if type(i) is dict:
                print '%s-' % (' ' * indent)
                printdict(i, indent + step, step)
            elif type(i) in (list, tuple):
                printlist(i, indent + step, step)
            else:
                print '%s- %s' % (' ' * indent, str(i))
        print '%s]' % (' ' * indent)                    
    def printdict(d, indent=0, step=2):
        for k, v in d.iteritems():
            if type(v) is dict:
                print '%s%s:' % (' ' * indent, str(k))
                printdict(v, indent + step, step)
            elif type(v) in (list, tuple):
                print '%s%s:' % (' ' * indent, str(k))
                printlist(v, indent + step, step)
            else:
                print '%s%s: %s' % (' ' * indent, str(k), str(v))
    printdict(choice, step=step)





nodes = ['s1', 's2']#, 's3', 's4']
interfaces = ['0', '1']

arcs = getArcs(nodes, interfaces)

#print arcs
netcheck = NetChecker(nodes, arcs)
choices = netcheck.get_choices()

for i in xrange(len(choices)):
    print "\n---- Choice number %d: ----\n" % (i + 1)
    printChoice(choices[i])
