from cctbx.examples import phase_o_phrenia
from cctbx.array_family import flex
from cctbx.web import io_utils
from cctbx.web import cgi_utils

def interpret_form_data(form):
  inp = cgi_utils.inp_from_form(form,
    (("ucparams", "1 1 1 90 90 90"),
     ("sgsymbol", "P1"),
     ("convention", ""),
     ("format", None),
     ("coor_type", None),
     ("coor_file", None),
     ("coordinates", None),
     ("min_distance_sym_equiv", "0.5"),
     ("d_min", "3"),
     ("min_peak_distance", "4.0"),
     ("max_reduced_peaks", "60")))
  inp.coordinates = cgi_utils.coordinates_from_form(form)
  return inp

def run(server_info, inp, status):
  print "<pre>"
  special_position_settings = io_utils.special_position_settings_from_inp(inp)
  special_position_settings.show_summary()
  print "Minimum distance between symmetrically equivalent sites:",
  print special_position_settings.min_distance_sym_equiv()
  print

  if (inp.format == "cns_sdb"):
    raise RuntimeError, "Not implemented." # XXX

  structure = io_utils.structure_from_inp(inp, status, special_position_settings)

  d_min = float(inp.d_min)
  print "Minimum d-spacing:", d_min
  if (d_min <= 0.):
    raise ValueError, "d-spacing must be greater than zero."
  print

  min_peak_distance = float(inp.min_peak_distance)
  print "Minimum peak distance:", min_peak_distance
  if (min_peak_distance <= 0.):
    raise ValueError, "min_peak_distance must be greater than zero."
  print

  max_reduced_peaks = int(inp.max_reduced_peaks)
  print "Maximum number of peaks:", max_reduced_peaks
  if (max_reduced_peaks <= 0):
    raise ValueError, "max_reduced_peaks must be greater than zero."
  print

  reduced_peaks = phase_o_phrenia.calculate_exp_i_two_phi_peaks(
    xray_structure=structure,
    d_min=d_min,
    min_peak_distance=min_peak_distance,
    max_reduced_peaks=max_reduced_peaks)

  print "Actual number of peaks:", len(reduced_peaks)
  print

  plot_nx = min(len(reduced_peaks), 60)
  if (plot_nx > 0):
    plot_ny = max(10, plot_nx/3)
    if (plot_nx != max_reduced_peaks):
      print "Number of peaks used for plot:", plot_nx
      print
    print "Plot of relative peak heights:"
    print
    plot = flex.bool(flex.grid(plot_nx, plot_ny))
    for i in xrange(plot_nx):
      height = reduced_peaks[i].height
      h = int(round(height * plot_ny))
      h = max(0, min(plot_ny, h))
      for j in xrange(h): plot[(i,j)] = 0001
    for j in xrange(plot_ny-1,-1,-1):
      line = ""
      for i in xrange(plot_nx):
        if (plot[(i,j)]): line += "*"
        else:                  line += " "
      print "    |" + line.rstrip()
    print   "    -" + "-" * plot_nx
    print

    print "Peak list:"
    print "  Relative"
    print "   height   Fractional coordinates"
    for peak in reduced_peaks:
      print "    %5.1f" % (peak.height*100), " %8.5f %8.5f %8.5f" % peak.site
    print

  print "</pre>"
