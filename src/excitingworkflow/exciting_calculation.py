class ExcitingCalculation(CalculationIO):
    def __init__(self,
                 name,
                 dir
                 runner,
                 structure,
                 ground_state
                 bse: Optional):

    def write_inputs(self):
        write_input_xml(self)
        # TODO Copy (from some well-defined place) and write species files

    def write_input_xml(self):
        xml_tree = exciting_input_xml(structure, ground_state, bse=bse, title=self.name)
        xml_string = ET.tostring(xml_tree)
        with open(file=self.dir + "/input.xml", "w") as fid:
            fid.write(xml_string)

    def run(self) -> SubprocessRunResults:
        """ Wrapper for simple BinaryRunner.

        :return: Subprocess results or NotImplementedError.
        """
        return self.runner.run()

    def parse_output(self) -> Union[dict, FileNotFoundError]:
        """ 
        """
        info_out: dict = groundstate_parser.parse_info_out("INFO.OUT")
        eps_singlet = bse_parser.parse_EPSILON_NAR("file_name")
        return {**info_out, **eps_singlet}
        
        
def set_gqmax(gq_max: float, calculation: ExcitingCalculation):
    new_calculation = copy.deepcopy(calculation)
    new_calculation.bse.gq_max = gq_max
    new_calculation.write_input_xml()
    
