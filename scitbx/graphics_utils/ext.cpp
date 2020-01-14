
#include <scitbx/graphics_utils/colors.h>

#include <boost/python/module.hpp>
#include <boost/python/def.hpp>
#include <boost/python/class.hpp>
#include <boost/python/args.hpp>

namespace scitbx { namespace graphics_utils {
namespace {

  void init_module ()
  {
    using namespace boost::python;
                def("NoNansvec3", NoNansvec3, (
                        arg("vecs"),
                        arg("defx") = 0.0,
                        arg("defy") = 0.0,
                        arg("defz") = 0.0
                        ));
                def("IsNansvec3", IsNansvec3, (
                        arg("vecs")));
                def("NoNans", NoNans, (
                        arg("arr"),
                        arg("def") = 0.0));
                def("IsNans", IsNans, (
                        arg("arr")));
                def("make_rainbow_gradient", make_rainbow_gradient, (
                        arg("nbins")));
                def("color_rainbow", color_rainbow, (
      arg("selection"),
      arg("color_all")=false));
    def("color_by_property_", color_by_property, (
      arg("properties"),
      arg("selection"),
      arg("color_all") = true,
      arg("gradient_type") = 0,
      arg("min_value") = 0.1));
    def("color_by_phi_fom_", color_by_phi_fom, (
      arg("phases"),
      arg("foms")));
    def("grayscale_by_property", grayscale_by_property, (
      arg("properties"),
      arg("selection"),
      arg("shade_all")=false,
      arg("invert")=false,
      arg("max_value")=0.95,
      arg("max_value_inverted")=0.1));
    def("scale_selected_colors", scale_selected_colors, (
      arg("input_colors"),
      arg("selection"),
      arg("scale")=0.5));
  }
}
}}

BOOST_PYTHON_MODULE(scitbx_graphics_utils_ext)
{
  scitbx::graphics_utils::init_module();
}
