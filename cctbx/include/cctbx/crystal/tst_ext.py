from cctbx import crystal
import cctbx.crystal.coordination_sequences
from cctbx import sgtbx
import cctbx.crystal.direct_space_asu
from cctbx import uctbx
from cctbx.array_family import flex
from scitbx import matrix
from libtbx.test_utils import approx_equal
from libtbx.itertbx import count
from cStringIO import StringIO
import md5
import sys

def trial_structure():
  from cctbx import xray
  return xray.structure(
    crystal_symmetry=crystal.symmetry(
      unit_cell="12.548 12.548 20.789 90.000 90.000 120.000",
      space_group_symbol="P63/mmc"),
    scatterers=flex.xray_scatterer(
      [xray.scatterer(label="Si", site=site) for site in [
        (0.2466,0.9965,0.2500),
        (0.5817,0.6706,0.1254),
        (0.2478,0.0000,0.0000)]]))

def exercise_direct_space_asu():
  cp = crystal.direct_space_asu.float_cut_plane(n=[-1,0,0], c=1)
  assert approx_equal(cp.n, [-1,0,0])
  assert approx_equal(cp.c, 1)
  assert approx_equal(cp.evaluate(point=[0,2,3]), 1)
  assert approx_equal(cp.evaluate(point=[1,2,3]), 0)
  assert cp.is_inside(point=[0.99,0,0], epsilon=0)
  assert not cp.is_inside([1.01,0,0])
  assert approx_equal(cp.get_point_in_plane(), [1,0,0])
  cp.n = [0,-1,0]
  assert approx_equal(cp.n, [0,-1,0])
  cp.c = 2
  assert approx_equal(cp.c, 2)
  assert approx_equal(cp.get_point_in_plane(), [0,2,0])
  unit_cell = uctbx.unit_cell((1,1,1,90,90,90))
  cpb = cp.add_buffer(unit_cell=unit_cell, thickness=0.5)
  assert approx_equal(cpb.n, cp.n)
  assert approx_equal(cpb.c, 2.5)
  asu = crystal.direct_space_asu_float_asu(
    unit_cell=unit_cell,
    facets=[])
  assert asu.volume_vertices().size() == 0
  facets = []
  for i in xrange(3):
    n = [0,0,0]
    n[i] = -1
    facets.append(crystal.direct_space_asu.float_cut_plane(n=n, c=i+1))
  asu = crystal.direct_space_asu.float_asu(
    unit_cell=unit_cell,
    facets=facets,
    is_inside_epsilon=1.e-6)
  assert asu.unit_cell().is_similar_to(unit_cell)
  for i in xrange(3):
    n = [0,0,0]
    n[i] = -1
    assert approx_equal(asu.facets()[i].n, n)
    assert approx_equal(asu.facets()[i].c, i+1)
  assert approx_equal(asu.is_inside_epsilon(), 1.e-6)
  assert asu.is_inside([0.99,0.49,0.32])
  eps = 0.02
  assert not asu.is_inside([0.99+eps,0.49+eps,0.32+eps])
  buf_asu = asu._add_buffer(0.2)
  assert buf_asu.is_inside([0.99+0.2,0.49+0.2,0.32+0.2])
  eps = 0.02
  assert not buf_asu.is_inside([0.99+0.2+eps,0.49+0.2+eps,0.32+0.2+eps])
  assert len(asu.volume_vertices()) == 1
  for cartesian in [False,True]:
    assert approx_equal(asu.volume_vertices(
      cartesian=cartesian, epsilon=1.e-6)[0], (1.0, 2.0, 3.0))
  asu = crystal.direct_space_asu.float_asu(
    unit_cell=unit_cell,
    facets=[crystal.direct_space_asu.float_cut_plane(n=n,c=c) for n,c in [
      [(0, 0, 1), -1/2.],
      [(-1, -1, 0), 1],
      [(0, 1, -1), 3/4.],
      [(1, 0, -1), 1/4.]]])
  assert approx_equal(asu.box_min(), [0.25, -0.25, 0.5])
  assert approx_equal(asu.box_max(), [1.25, 0.75, 1.0])
  assert approx_equal(asu.box_min(cartesian=True), [0.25, -0.25, 0.5])
  assert approx_equal(asu.box_max(cartesian=True), [1.25, 0.75, 1.0])
  asu_mappings = crystal.direct_space_asu.asu_mappings(
    space_group=sgtbx.space_group("P 2 3").change_basis(
      sgtbx.change_of_basis_op("x+1/4,y-1/4,z+1/2")),
    asu=asu,
    buffer_thickness=0.1)
  asu_mappings.reserve(n_sites_final=10)
  assert asu_mappings.space_group().order_z() == 12
  assert len(asu_mappings.asu().facets()) == 4
  assert asu_mappings.unit_cell().is_similar_to(unit_cell)
  assert approx_equal(asu_mappings.buffer_thickness(), 0.1)
  assert approx_equal(asu_mappings.asu_buffer().box_min(),
    [0.0085786, -0.4914214, 0.4])
  assert approx_equal(asu_mappings.buffer_covering_sphere().radius(),0.8071081)
  sites_seq = [
    [3.1,-2.2,1.3],
    [-4.3,1.7,0.4]]
  assert asu_mappings.mappings().size() == 0
  assert asu_mappings.process(
    original_site=sites_seq[0],
    min_distance_sym_equiv=0.01) is asu_mappings
  assert asu_mappings.mappings().size() == 1
  site_symmetry = sgtbx.site_symmetry(
    unit_cell=asu_mappings.asu().unit_cell(),
    space_group=asu_mappings.space_group(),
    original_site=sites_seq[1],
    min_distance_sym_equiv=0.01)
  assert asu_mappings.process(
    original_site=sites_seq[1],
    site_symmetry_ops=site_symmetry) is asu_mappings
  assert asu_mappings.mappings().size() == 2
  sites_frac = flex.vec3_double([m[1-i].mapped_site()
    for i,m in enumerate(asu_mappings.mappings())])
  assert list(asu_mappings.asu().is_inside_frac(
    sites_frac=sites_frac)) == [False, True]
  assert list(asu_mappings.asu().is_inside_cart(
    sites_cart=asu_mappings.asu().unit_cell().orthogonalization_matrix()
              *sites_frac)) == [False, True]
  assert asu_mappings.n_sites_in_asu_and_buffer() == 11
  assert not asu_mappings.is_locked()
  asu_mappings.lock()
  assert asu_mappings.is_locked()
  try: asu_mappings.process(original_site=[0,0,0])
  except RuntimeError, e: assert str(e).find("is_locked") > 0
  else: raise RuntimeError("Exception expected.")
  mappings = asu_mappings.mappings()[0]
  assert len(mappings) == 5
  am = mappings[0]
  assert am.i_sym_op() == 3
  assert am.unit_shifts() == (1,3,2)
  assert asu.is_inside(am.mapped_site())
  assert approx_equal(asu_mappings.mapped_sites_min(), [0.15,-0.4,0.4])
  assert approx_equal(asu_mappings.mapped_sites_max(), [1.05,0.6,0.65])
  assert approx_equal(asu_mappings.mapped_sites_span(), [0.9,1.0,0.25])
  assert list(asu_mappings.site_symmetry_table().indices()) == [0, 0]
  for am in mappings:
    assert asu_mappings.asu_buffer().is_inside(am.mapped_site())
  o = matrix.sqr(asu_mappings.unit_cell().orthogonalization_matrix())
  f = matrix.sqr(asu_mappings.unit_cell().fractionalization_matrix())
  for i_seq,m_i_seq in enumerate(asu_mappings.mappings()):
    for i_sym in xrange(len(m_i_seq)):
      rt_mx = asu_mappings.get_rt_mx(i_seq, i_sym)
      assert asu_mappings.get_rt_mx(asu_mappings.mappings()[i_seq][i_sym]) \
          == rt_mx
      site_frac = rt_mx * sites_seq[i_seq]
      site_cart = asu_mappings.unit_cell().orthogonalize(site_frac)
      assert approx_equal(m_i_seq[i_sym].mapped_site(), site_cart)
      assert approx_equal(
        asu_mappings.map_moved_site_to_asu(
          moved_original_site
            =asu_mappings.unit_cell().orthogonalize(sites_seq[i_seq]),
          i_seq=i_seq,
          i_sym=i_sym),
        site_cart)
      r = matrix.sqr(rt_mx.r().inverse().as_double())
      assert approx_equal(
        asu_mappings.r_inv_cart(i_seq=i_seq, i_sym=i_sym),
        (o*r*f).elems)
  pair_generator = crystal.neighbors_simple_pair_generator(asu_mappings)
  assert not pair_generator.at_end()
  assert len(asu_mappings.mappings()[1]) == 6
  index_pairs = []
  for index_pair in pair_generator:
    index_pairs.append((index_pair.i_seq, index_pair.j_seq, index_pair.j_sym))
    assert index_pair.dist_sq == -1
    assert not pair_generator.is_simple_interaction(index_pair)
  assert pair_generator.at_end()
  assert index_pairs == [
    (0,0,1),(0,0,2),(0,0,3),(0,0,4),
    (0,1,0),(0,1,1),(0,1,2),(0,1,3),(0,1,4),(0,1,5),
    (1,0,1),(1,0,2),(1,0,3),(1,0,4),
    (1,1,1),(1,1,2),(1,1,3),(1,1,4),(1,1,5)]
  for two_flag,buffer_thickness,expected_index_pairs,expected_n_boxes in [
    (False, 0.04, [], (1,1,1)),
    (False, 0.1, [(0,0,1),(0,0,2),(0,0,3),(0,0,4)], (2,3,1)),
    (True, 0, [(0, 1, 0)], (1,1,1)),
    (True, 0.04, [(0, 1, 0), (0, 1, 1), (1, 1, 1)], (1,2,1))]:
    asu_mappings = crystal.direct_space_asu.asu_mappings(
      space_group=sgtbx.space_group("P 2 3").change_basis(
        sgtbx.change_of_basis_op("x+1/4,y-1/4,z+1/2")),
      asu=asu,
      buffer_thickness=buffer_thickness)
    assert asu_mappings.process_sites_frac(
      original_sites=flex.vec3_double([[3.1,-2.2,1.3]]),
      min_distance_sym_equiv=0.01) is asu_mappings
    assert asu_mappings.mappings().size() == 1
    if (two_flag):
      assert asu_mappings.process_sites_cart(
        original_sites=flex.vec3_double([
          asu.unit_cell().orthogonalize([-4.3,1.7,0.4])]),
        min_distance_sym_equiv=0.01) is asu_mappings
    pair_generator = crystal.neighbors_simple_pair_generator(asu_mappings)
    index_pairs = []
    for index_pair in pair_generator:
      index_pairs.append((index_pair.i_seq,index_pair.j_seq,index_pair.j_sym))
      assert index_pair.dist_sq == -1
    assert pair_generator.at_end()
    assert index_pairs == expected_index_pairs
    pair_generator.restart()
    if (len(expected_index_pairs) == 0):
      assert pair_generator.at_end()
    else:
      assert not pair_generator.at_end()
    assert pair_generator.count_pairs() == len(index_pairs)
    pair_generator.restart()
    if (two_flag):
      assert pair_generator.neighbors_of(
        primary_selection=flex.bool([True,False])).count(True) == 2
    pair_generator.restart()
    index_pairs = []
    for index_pair in pair_generator:
      index_pairs.append((index_pair.i_seq,index_pair.j_seq,index_pair.j_sym))
      assert index_pair.dist_sq == -1
    assert pair_generator.at_end()
    assert index_pairs == expected_index_pairs
    simple_pair_generator = crystal.neighbors_simple_pair_generator(
      asu_mappings=asu_mappings,
      distance_cutoff=100,
      minimal=False)
    assert simple_pair_generator.asu_mappings().is_locked()
    assert approx_equal(simple_pair_generator.distance_cutoff_sq(), 100*100)
    fast_pair_generator = crystal.neighbors_fast_pair_generator(
      asu_mappings=asu_mappings,
      distance_cutoff=100,
      minimal=False,
      epsilon=1.e-6)
    assert fast_pair_generator.asu_mappings().is_locked()
    assert approx_equal(fast_pair_generator.distance_cutoff_sq(), 100*100)
    assert approx_equal(fast_pair_generator.epsilon()/1.e-6, 1)
    assert fast_pair_generator.n_boxes() == (1,1,1)
    index_pairs = []
    dist_sq = flex.double()
    for index_pair in simple_pair_generator:
      index_pairs.append((index_pair.i_seq,index_pair.j_seq,index_pair.j_sym))
      assert index_pair.dist_sq > 0
      assert approx_equal(
        asu_mappings.diff_vec(pair=index_pair),
        index_pair.diff_vec)
      assert approx_equal(
        matrix.col(asu_mappings.diff_vec(pair=index_pair)).norm_sq(),
        index_pair.dist_sq)
      dist_sq.append(index_pair.dist_sq)
    assert simple_pair_generator.at_end()
    assert index_pairs == expected_index_pairs
    if (len(index_pairs) == 0):
      assert fast_pair_generator.at_end()
    else:
      assert not fast_pair_generator.at_end()
    index_pairs = []
    for index_pair in fast_pair_generator:
      index_pairs.append((index_pair.i_seq,index_pair.j_seq,index_pair.j_sym))
    assert index_pairs == expected_index_pairs
    assert fast_pair_generator.at_end()
    distances = flex.sqrt(dist_sq)
    if (distances.size() > 0):
      cutoff = flex.mean(distances) + 1.e-5
    else:
      cutoff = 0
    short_dist_sq = dist_sq.select(distances <= cutoff)
    for pair_generator_type in [crystal.neighbors_simple_pair_generator,
                                crystal.neighbors_fast_pair_generator]:
      if (    pair_generator_type is crystal.neighbors_fast_pair_generator
          and cutoff == 0): continue
      pair_generator = pair_generator_type(
        asu_mappings=asu_mappings,
        distance_cutoff=cutoff)
      index_pairs = []
      dist_sq = flex.double()
      for index_pair in pair_generator:
        index_pairs.append((index_pair.i_seq,index_pair.j_seq,index_pair.j_sym))
        assert index_pair.dist_sq > 0
        assert approx_equal(
          asu_mappings.diff_vec(pair=index_pair),
          index_pair.diff_vec)
        assert approx_equal(
          matrix.col(asu_mappings.diff_vec(pair=index_pair)).norm_sq(),
          index_pair.dist_sq)
        assert not asu_mappings.is_simple_interaction(pair=index_pair)
        dist_sq.append(index_pair.dist_sq)
      assert pair_generator.at_end()
      if (pair_generator_type is crystal.neighbors_simple_pair_generator):
        assert approx_equal(dist_sq, short_dist_sq)
      else:
        assert pair_generator.n_boxes() == expected_n_boxes
        short_dist_sq_sorted = short_dist_sq.select(
          flex.sort_permutation(data=short_dist_sq))
        dist_sq_sorted = dist_sq.select(
          flex.sort_permutation(data=dist_sq))
        assert approx_equal(dist_sq_sorted, short_dist_sq_sorted)
      assert pair_generator.count_pairs() == 0
      assert pair_generator.max_distance_sq() == -1
      pair_generator.restart()
      assert pair_generator.count_pairs() == len(index_pairs)
      pair_generator.restart()
      if (len(index_pairs) == 0):
        assert pair_generator.max_distance_sq() == -1
      else:
        assert approx_equal(pair_generator.max_distance_sq(), 0.1)
      pair_generator.restart()
      primary_selection = flex.bool(
        pair_generator.asu_mappings().mappings().size(), False)
      primary_selection[0] = True
      assert pair_generator.neighbors_of(
        primary_selection=primary_selection).count(False) == 0
  pair = asu_mappings.make_trial_pair(i_seq=1, j_seq=0, j_sym=0)
  assert pair.i_seq == 1
  assert pair.j_seq == 0
  assert pair.j_sym == 0
  assert not pair.is_active()
  pair = asu_mappings.make_pair(i_seq=0, j_seq=1, j_sym=1)
  assert pair.i_seq == 0
  assert pair.j_seq == 1
  assert pair.j_sym == 1
  assert pair.is_active()
  from cctbx import xray
  structure = trial_structure()
  asu_mappings = structure.asu_mappings(buffer_thickness=3.5)
  assert list(asu_mappings.site_symmetry_table().indices()) == [1,0,2]
  assert asu_mappings.n_sites_in_asu_and_buffer() == 33
  pair = asu_mappings.make_pair(i_seq=1, j_seq=0, j_sym=1)
  assert pair.i_seq == 1
  assert pair.j_seq == 0
  assert pair.j_sym == 1
  assert pair.is_active(minimal=False)
  assert not pair.is_active(minimal=True)
  for i_seq,m in enumerate(asu_mappings.mappings()):
    for i_sym in xrange(len(m)):
      rt_mx = asu_mappings.get_rt_mx(i_seq=i_seq, i_sym=i_sym)
      i_sym_found = asu_mappings.find_i_sym(i_seq=i_seq, rt_mx=rt_mx)
      assert i_sym_found == i_sym
      i_sym_found = asu_mappings.find_i_sym(
        i_seq=i_seq,
        rt_mx=sgtbx.rt_mx("0,0,0"))
      assert i_sym_found == -1
      if (i_sym != 0):
        pair_i_seq = max(0, i_seq-1)
        pair = asu_mappings.make_trial_pair(pair_i_seq, i_seq, i_sym)
        assert asu_mappings.get_rt_mx_i(pair=pair) \
            == asu_mappings.get_rt_mx(pair_i_seq, 0)
        assert asu_mappings.get_rt_mx_j(pair=pair) \
            == asu_mappings.get_rt_mx(i_seq, i_sym)
  assert str(asu_mappings.special_op(0)) == "x,y,1/4"
  assert str(asu_mappings.special_op(1)) == "x,y,z"
  assert str(asu_mappings.special_op(2)) == "x-1/2*y,0,0"
  asu_mappings = structure[:0].asu_mappings(buffer_thickness=3.5)
  assert asu_mappings.process_sites_frac(
    original_sites=structure.scatterers().extract_sites()) is asu_mappings
  assert asu_mappings.n_sites_in_asu_and_buffer() == 33
  asu_mappings = structure[:0].asu_mappings(buffer_thickness=3.5)
  assert asu_mappings.process_sites_frac(
    original_sites=structure.scatterers().extract_sites(),
    site_symmetry_table=structure.site_symmetry_table()) is asu_mappings
  assert asu_mappings.n_sites_in_asu_and_buffer() == 33
  asu_mappings = structure[:0].asu_mappings(buffer_thickness=3.5)
  assert asu_mappings.process_sites_cart(
    original_sites=structure.sites_cart()) is asu_mappings
  assert asu_mappings.n_sites_in_asu_and_buffer() == 33
  asu_mappings = structure[:0].asu_mappings(buffer_thickness=3.5)
  assert asu_mappings.process_sites_cart(
    original_sites=structure.sites_cart(),
    site_symmetry_table=structure.site_symmetry_table()) is asu_mappings
  assert asu_mappings.n_sites_in_asu_and_buffer() == 33

def check_pair_asu_table(asu_table, expected_asu_pairs):
  ip = count()
  for i_seq,asu_dict in enumerate(asu_table.table()):
    for j_seq,j_sym_groups in asu_dict.items():
      for j_sym_group in j_sym_groups:
        for j_sym in j_sym_group:
          if (0 or "--Verbose" in sys.argv[1:] or expected_asu_pairs is None):
            print str([i_seq, j_seq, j_sym]) + ","
          if (expected_asu_pairs is not None):
            assert [i_seq, j_seq, j_sym] == expected_asu_pairs[ip.next()]

def exercise_pair_tables():
  d = crystal.pair_sym_dict()
  assert len(d) == 0
  sym_ops = sgtbx.space_group("P 41").all_ops()
  for i,j_sym in enumerate([10,18,13]):
    d[j_sym] = crystal.pair_sym_ops(sym_ops[:i])
    assert len(d) == i+1
    assert len(d[j_sym]) == i
    assert [str(s) for s in sym_ops[:i]] == [str(s) for s in d[j_sym]]
    d[j_sym] = sym_ops[:i]
    assert [str(s) for s in sym_ops[:i]] == [str(s) for s in d[j_sym]]
  assert [key for key in d] == [10,13,18]
  assert d[13].size() == 2
  d[13].append(sym_ops[-1])
  assert d[13].size() == 3
  del d[13][0]
  assert d[13].size() == 2
  d[13].clear()
  assert d[13].size() == 0
  t = crystal.pair_sym_table()
  t.append(d)
  assert t.size() == 1
  assert len(t[0][10]) == 0
  t.append(d)
  assert t.size() == 2
  assert len(t[1][18]) == 1
  t = crystal.pair_sym_table(3)
  for d in t:
    assert len(d) == 0
  t[1][10] = sym_ops[:2]
  assert len(t[1]) == 1
  assert len(t[1][10]) == 2
  #
  t = crystal.pair_asu_table_table(3)
  for d in t:
    assert len(d) == 0
  t[1][10] = crystal.pair_asu_j_sym_groups()
  assert t[1][10].size() == 0
  t[1][10].append(crystal.pair_asu_j_sym_group())
  assert t[1][10].size() == 1
  assert t[1][10][0].size() == 0
  t[1][10][0].insert(3)
  assert t[1][10][0].size() == 1
  t[1][10].append(crystal.pair_asu_j_sym_group())
  assert t[1][10][1].size() == 0
  t[1][10][1].insert([4,5,4])
  assert t[1][10][1].size() == 2
  #
  structure = trial_structure()
  asu_mappings = structure.asu_mappings(buffer_thickness=3.5)
  asu_table = crystal.pair_asu_table(asu_mappings=asu_mappings)
  assert asu_table.asu_mappings().is_locked()
  assert asu_table.table().size() == 3
  assert not asu_table.contains(i_seq=0, j_seq=1, j_sym=2)
  assert asu_table.pair_counts().all_eq(0)
  assert asu_table.add_all_pairs(distance_cutoff=3.5) is asu_table
  assert [d.size() for d in asu_table.table()] == [2,3,2]
  assert asu_table.add_all_pairs(3.5, epsilon=1.e-6) is asu_table
  assert [d.size() for d in asu_table.table()] == [2,3,2]
  expected_asu_pairs = [
    [0, 0, 2], [0, 0, 1], [0, 1, 0], [0, 1, 8],
    [1, 0, 0], [1, 1, 4], [1, 1, 1], [1, 2, 0],
    [2, 1, 0], [2, 1, 11], [2, 2, 1], [2, 2, 2]]
  check_pair_asu_table(asu_table, expected_asu_pairs)
  asu_table = crystal.pair_asu_table(asu_mappings=asu_mappings)
  for minimal in [True, False]:
    pair_generator = crystal.neighbors_fast_pair_generator(
      asu_mappings,
      distance_cutoff=3.5,
      minimal=minimal)
    for pair in pair_generator:
      asu_table.add_pair(pair=pair)
    asu_table.pair_counts().all_eq(4)
    check_pair_asu_table(asu_table, expected_asu_pairs)
  for p in expected_asu_pairs:
    assert asu_table.contains(i_seq=p[0], j_seq=p[1], j_sym=p[2])
    pair = asu_mappings.make_trial_pair(*p)
    assert pair in asu_table
  f = StringIO()
  asu_table.show(f=f)
  assert f.getvalue() == """\
i_seq: 0
  j_seq: 0
    j_syms: [2]
    j_syms: [1]
  j_seq: 1
    j_syms: [0, 8]
i_seq: 1
  j_seq: 0
    j_syms: [0]
  j_seq: 1
    j_syms: [4]
    j_syms: [1]
  j_seq: 2
    j_syms: [0]
i_seq: 2
  j_seq: 1
    j_syms: [0, 11]
  j_seq: 2
    j_syms: [1, 2]
"""
  f = StringIO()
  asu_table.show(
    f=f,
    site_labels=[scatterer.label for scatterer in structure.scatterers()])
  assert f.getvalue() == """\
Si(0)
  Si(0)
    j_syms: [2]
    j_syms: [1]
  Si(1)
    j_syms: [0, 8]
Si(1)
  Si(0)
    j_syms: [0]
  Si(1)
    j_syms: [4]
    j_syms: [1]
  Si(2)
    j_syms: [0]
Si(2)
  Si(1)
    j_syms: [0, 11]
  Si(2)
    j_syms: [1, 2]
"""
  assert not asu_table.contains(i_seq=1, j_seq=1, j_sym=10)
  pair = asu_mappings.make_trial_pair(i_seq=1, j_seq=1, j_sym=10)
  assert not pair in asu_table
  assert asu_table == asu_table
  assert not asu_table != asu_table
  other = crystal.pair_asu_table(asu_mappings=asu_mappings)
  assert not asu_table == other
  assert asu_table != other
  for skip_j_seq_less_than_i_seq in [False, True]:
    sym_table = asu_table.extract_pair_sym_table(
      skip_j_seq_less_than_i_seq=skip_j_seq_less_than_i_seq)
    assert sym_table.size() == asu_table.table().size()
    expected_sym_pairs = [
      [0, 0, '-y+1,-x+1,-z+1/2'],
      [0, 0, 'x,x-y+2,-z+1/2'],
      [0, 1, '-y+1,x-y+1,-z+1/2'],
        [1, 0, '-x+y,-x+1,-z+1/2'],
      [1, 1, 'x,x-y+1,z'],
      [1, 1, '-y+1,-x+1,z'],
      [1, 2, '-x+1,-x+y+1,-z'],
        [2, 1, '-x+1,-x+y,-z'],
      [2, 2, 'y,-x+y,-z']]
    ip = count()
    for i_seq,sym_dict in enumerate(sym_table):
      for j_seq,rt_mx_list in sym_dict.items():
        for rt_mx in rt_mx_list:
          while 1:
            expected = expected_sym_pairs[ip.next()]
            if (not (skip_j_seq_less_than_i_seq and expected[1]<expected[0])):
              break
          if (0 or "--Verbose" in sys.argv[1:]):
            print str([i_seq, j_seq, str(rt_mx)]) + ","
          assert [i_seq, j_seq, str(rt_mx)] == expected
    asu_table = crystal.pair_asu_table(asu_mappings=asu_mappings)
    assert asu_table.add_pair_sym_table(sym_table=sym_table) is asu_table
    check_pair_asu_table(asu_table, expected_asu_pairs)
    eq_flags = []
    asu_table_2 = crystal.pair_asu_table(asu_mappings=asu_mappings)
    for p in expected_sym_pairs:
      assert asu_table_2.add_pair(
        i_seq=p[0], j_seq=p[1], rt_mx_ji=sgtbx.rt_mx(p[2])) is asu_table_2
      eq_flags.append(asu_table_2 == asu_table)
      assert (asu_table_2 == asu_table) != (asu_table_2 != asu_table)
    check_pair_asu_table(asu_table_2, expected_asu_pairs)
    assert eq_flags[:-1].count(eq_flags[0]) == len(eq_flags)-1
    assert eq_flags[-1]
    ### exercise adp_iso_restraint_helper, begin
    omx = structure.unit_cell().orthogonalization_matrix()
    u_isos = flex.double([0.01,0.09,0.1])
    obj = crystal.adp_iso_restraint_helper(
                             pair_sym_table           = sym_table,
                             orthogonalization_matrix = omx,
                             sites_frac               = structure.sites_frac(),
                             u_isos                   = u_isos,
                             sphere_radius            = 5.0,
                             distance_power           = 0.7,
                             mean_power               = 0.5,
                             normalize                = True)
    target = obj.target()
    gradients = obj.derivatives()
    counter = obj.number_of_members()
    case_1 = approx_equal(target, 0.00202796953554, out=None)
    case_2 = approx_equal(target, 0.00130369470142, out=None)
    assert [case_1,case_2].count(True) == 1
    case_1 = approx_equal(gradients, [-0.060161352769129386, \
                        0.035529896242978656, 0.0044587716913385769], out=None)
    case_2 = approx_equal(gradients, [-0.038675155351583175, \
                        0.022840647584771993, 0.0028663532301462279], out=None)
    assert [case_1,case_2].count(True) == 1
    case_1 = approx_equal(counter, 9, out=None)
    case_2 = approx_equal(counter, 7, out=None)
    assert [case_1,case_2].count(True) == 1
    ### exercise adp_iso_restraint_helper, end
    distances = crystal.get_distances(
      pair_sym_table=sym_table,
      orthogonalization_matrix
        =structure.unit_cell().orthogonalization_matrix(),
      sites_frac=structure.sites_frac())
    if (not skip_j_seq_less_than_i_seq):
      assert approx_equal(distances,
        [3.0504188000000001, 3.1821727999999987, 3.1703090658301503,
         3.1703090658301503, 3.0177940000000003, 3.1658603999999984,
         3.1986122507292754, 3.1986122507292754, 3.1093943999999989])
    else:
      assert approx_equal(distances,
        [3.0504188000000001, 3.1821727999999987, 3.1703090658301503,
         3.0177940000000003, 3.1658603999999984, 3.1986122507292754,
         3.1093943999999989])
      f = StringIO()
      sym_table.show(f=f)
      assert f.getvalue() == """\
i_seq: 0
  j_seq: 0
    -y+1,-x+1,-z+1/2
    x,x-y+2,-z+1/2
  j_seq: 1
    -y+1,x-y+1,-z+1/2
i_seq: 1
  j_seq: 1
    x,x-y+1,z
    -y+1,-x+1,z
  j_seq: 2
    -x+1,-x+y+1,-z
i_seq: 2
  j_seq: 2
    y,-x+y,-z
"""
      f = StringIO()
      sym_table.show(
        f=f,
        site_labels=[scatterer.label for scatterer in structure.scatterers()])
      assert f.getvalue() == """\
Si(0)
  Si(0)
    -y+1,-x+1,-z+1/2
    x,x-y+2,-z+1/2
  Si(1)
    -y+1,x-y+1,-z+1/2
Si(1)
  Si(1)
    x,x-y+1,z
    -y+1,-x+1,z
  Si(2)
    -x+1,-x+y+1,-z
Si(2)
  Si(2)
    y,-x+y,-z
"""
  #
  sites_cart = flex.vec3_double([(0,0,0), (2,0,0), (0,3,0)])
  asu_mappings = crystal.direct_space_asu.non_crystallographic_asu_mappings(
    sites_cart=sites_cart)
  bond_asu_table = crystal.pair_asu_table(asu_mappings=asu_mappings)
  bond_asu_table.add_all_pairs(distance_cutoff=3)
  f = StringIO()
  bond_asu_table.show(f=f)
  assert f.getvalue() == """\
i_seq: 0
  j_seq: 1
    j_syms: [0]
  j_seq: 2
    j_syms: [0]
i_seq: 1
  j_seq: 0
    j_syms: [0]
i_seq: 2
  j_seq: 0
    j_syms: [0]
"""
  sym_table = bond_asu_table.extract_pair_sym_table()
  f = StringIO()
  sym_table.show(f=f)
  assert f.getvalue() == """\
i_seq: 0
  j_seq: 1
    x,y,z
  j_seq: 2
    x,y,z
i_seq: 1
i_seq: 2
"""
  distances = crystal.get_distances(
    pair_sym_table=sym_table,
    sites_cart=sites_cart)
  assert approx_equal(distances, [2,3])
  #
  # Zeolite framework type ASV
  sym_table = crystal.pair_sym_table(5)
  d = sym_table[0].setdefault(0)
  d.append(sgtbx.rt_mx("x,y,-z"))
  d.append(sgtbx.rt_mx("-y+1,x,z"))
  d = sym_table[0].setdefault(1)
  d.append(sgtbx.rt_mx("x,y,z"))
  d = sym_table[0].setdefault(2)
  d.append(sgtbx.rt_mx("x,y,z"))
  d = sym_table[0].setdefault(3)
  d.append(sgtbx.rt_mx("x,y,z"))
  d.append(sgtbx.rt_mx("y,-x+1,z"))
  d = sym_table[0].setdefault(4)
  d.append(sgtbx.rt_mx("x,y,z"))
  d = sym_table[1].setdefault(4)
  d.append(sgtbx.rt_mx("x,y,z"))
  d = sym_table[2].setdefault(3)
  d.append(sgtbx.rt_mx("x,y,z"))
  d.append(sgtbx.rt_mx("y,-x+1,z"))
  d = sym_table[2].setdefault(4)
  d.append(sgtbx.rt_mx("x,y,z"))
  d = sym_table[3].setdefault(3)
  d.append(sgtbx.rt_mx("-y+1,x,z"))
  d = sym_table[3].setdefault(4)
  d.append(sgtbx.rt_mx("x,y,z"))
  d.append(sgtbx.rt_mx("-y+1,x,z"))
  d = sym_table[4].setdefault(4)
  d.append(sgtbx.rt_mx("x,-y+1,-z+1/2"))
  d.append(sgtbx.rt_mx("-x,y,-z+1/2"))
  d.append(sgtbx.rt_mx("-x,-y+1,z"))
  out = StringIO()
  sym_table.show(f=out)
  assert out.getvalue() == """\
i_seq: 0
  j_seq: 0
    x,y,-z
    -y+1,x,z
  j_seq: 1
    x,y,z
  j_seq: 2
    x,y,z
  j_seq: 3
    x,y,z
    y,-x+1,z
  j_seq: 4
    x,y,z
i_seq: 1
  j_seq: 4
    x,y,z
i_seq: 2
  j_seq: 3
    x,y,z
    y,-x+1,z
  j_seq: 4
    x,y,z
i_seq: 3
  j_seq: 3
    -y+1,x,z
  j_seq: 4
    x,y,z
    -y+1,x,z
i_seq: 4
  j_seq: 4
    x,-y+1,-z+1/2
    -x,y,-z+1/2
    -x,-y+1,z
"""
  out = StringIO()
  for i_seq in xrange(5):
    sym_table.proxy_select(flex.size_t([i_seq])).show(f=out)
  assert out.getvalue() == """\
i_seq: 0
  j_seq: 0
    x,y,-z
    -y+1,x,z
i_seq: 0
i_seq: 0
i_seq: 0
  j_seq: 0
    -y+1,x,z
i_seq: 0
  j_seq: 0
    x,-y+1,-z+1/2
    -x,y,-z+1/2
    -x,-y+1,z
"""
  out = StringIO()
  sym_table.proxy_select(flex.size_t([1,2,4])).show(f=out)
  assert out.getvalue() == """\
i_seq: 0
  j_seq: 2
    x,y,z
i_seq: 1
  j_seq: 2
    x,y,z
i_seq: 2
  j_seq: 2
    x,-y+1,-z+1/2
    -x,y,-z+1/2
    -x,-y+1,z
"""
  out = StringIO()
  sym_table.proxy_select(flex.size_t([3,0,2])).show(f=out)
  assert out.getvalue() == """\
i_seq: 0
  j_seq: 0
    -y+1,x,z
i_seq: 1
  j_seq: 0
    x,y,z
    y,-x+1,z
  j_seq: 1
    x,y,-z
    -y+1,x,z
  j_seq: 2
    x,y,z
i_seq: 2
  j_seq: 0
    x,y,z
    y,-x+1,z
"""

def exercise_coordination_sequences_simple():
  structure = trial_structure()
  asu_mappings = structure.asu_mappings(buffer_thickness=3.5)
  asu_table = crystal.pair_asu_table(asu_mappings=asu_mappings)
  asu_table.add_all_pairs(distance_cutoff=3.5)
  term_table = crystal.coordination_sequences.simple(
    pair_asu_table=asu_table,
    max_shell=5)
  assert [list(terms) for terms in term_table] \
      == [[1,4,10,20,34,54], [1,4,10,20,34,53], [1,4,10,20,34,54]]
  asu_mappings = structure.asu_mappings(buffer_thickness=12)
  asu_table = crystal.pair_asu_table(asu_mappings=asu_mappings)
  asu_table.add_pair(i_seqs=[0, 1])
  asu_table.add_pair([0, 2])
  asu_table.add_pair([1, 2])
  expected_asu_pairs = [
    [0, 1, 78], [0, 1, 121], [0, 2, 12], [0, 2, 72],
    [1, 0, 67], [1, 2, 67],
    [2, 0, 8], [2, 0, 79], [2, 1, 107], [2, 1, 120]]
  check_pair_asu_table(asu_table, expected_asu_pairs)

def exercise_coordination_sequences_shell_asu_tables():
  structure = trial_structure()
  asu_mappings = structure.asu_mappings(buffer_thickness=12)
  asu_table = crystal.pair_asu_table(asu_mappings=asu_mappings)
  asu_table.add_all_pairs(distance_cutoff=3.5)
  expected_asu_pairs = [
    [0, 0, 25], [0, 0, 3], [0, 1, 0], [0, 1, 64],
    [1, 0, 0], [1, 1, 27], [1, 1, 4], [1, 2, 0],
    [2, 1, 0], [2, 1, 83], [2, 2, 3], [2, 2, 25]]
  check_pair_asu_table(asu_table, expected_asu_pairs)
  shell_asu_tables = crystal.coordination_sequences.shell_asu_tables(
    pair_asu_table=asu_table,
    max_shell=3)
  check_pair_asu_table(shell_asu_tables[0], expected_asu_pairs)
  s = StringIO()
  structure.show_distances(pair_asu_table=shell_asu_tables[1], out=s)
  print >> s
  s1_sym_table = shell_asu_tables[1].extract_pair_sym_table(
    skip_j_seq_less_than_i_seq=False)
  s1_asu_table = crystal.pair_asu_table(asu_mappings=asu_mappings)
  s1_asu_table.add_pair_sym_table(sym_table=s1_sym_table)
  structure.show_distances(pair_asu_table=s1_asu_table, out=s)
  print >> s
  s = s.getvalue().replace("-0.0000", " 0.0000")
  if (md5.md5(s).hexdigest() != "2644729423835c824fafc53919d2ccf4"):
    sys.stderr.write(s)
    raise AssertionError("Unexpected show_distances() output.")

def exercise_symmetry():
  symmetry = crystal.ext.symmetry(
    unit_cell=uctbx.unit_cell([1,2,3,80,90,100]),
    space_group=sgtbx.space_group("P 2"))
  assert symmetry.unit_cell().is_similar_to(
    uctbx.unit_cell([1,2,3,80,90,100]))
  assert symmetry.space_group().order_z() == 2
  symmetry_cb = symmetry.change_basis(
    change_of_basis_op=sgtbx.change_of_basis_op("z,x,y"))
  assert symmetry_cb.unit_cell().is_similar_to(
    uctbx.unit_cell([3,1,2,100,80,90]))
  assert str(sgtbx.space_group_info(
    group=symmetry_cb.space_group())) == "P 2 1 1"

def run():
  exercise_direct_space_asu()
  exercise_pair_tables()
  exercise_coordination_sequences_simple()
  exercise_coordination_sequences_shell_asu_tables()
  exercise_symmetry()
  print "OK"

if (__name__ == "__main__"):
  run()
