import os
import tempfile
import unittest
from pathlib import Path

import image_utils
from pdf_builder import _latex_template_loads_package


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class LatexTemplatePackageTests(unittest.TestCase):
    def test_default_template_loads_layout_packages(self):
        template_path = PROJECT_ROOT / 'template.tex'

        self.assertTrue(_latex_template_loads_package(template_path, 'float'))
        self.assertTrue(_latex_template_loads_package(template_path, 'needspace'))

    def test_package_detection_handles_options_lists_and_comments(self):
        source = r'''
            % \usepackage{needspace}
            \usepackage[section]{placeins, float}
            \RequirePackage{
                graphicx,
                needspace
            }
        '''
        with tempfile.NamedTemporaryFile('w', suffix='.tex', encoding='utf-8') as template:
            template.write(source)
            template.flush()

            self.assertTrue(_latex_template_loads_package(template.name, 'float'))
            self.assertTrue(_latex_template_loads_package(template.name, 'needspace'))
            self.assertFalse(_latex_template_loads_package(template.name, 'booktabs'))

    def test_commented_package_is_not_detected(self):
        with tempfile.NamedTemporaryFile('w', suffix='.tex', encoding='utf-8') as template:
            template.write('% \\usepackage{float}\n')
            template.flush()

            self.assertFalse(_latex_template_loads_package(template.name, 'float'))

    def test_package_after_document_start_is_not_detected(self):
        with tempfile.NamedTemporaryFile('w', suffix='.tex', encoding='utf-8') as template:
            template.write(
                '\\documentclass{article}\n'
                '\\begin{document}\n'
                '\\usepackage{float}\n'
            )
            template.flush()

            self.assertFalse(_latex_template_loads_package(template.name, 'float'))


class FigurePlacementTests(unittest.TestCase):
    def test_figure_placement_can_fall_back_for_custom_templates(self):
        with tempfile.TemporaryDirectory() as book_dir, tempfile.TemporaryDirectory() as output_dir:
            image_path = Path(book_dir) / 'diagram.png'
            image_path.write_bytes(b'not-a-real-png')
            source_path = Path(book_dir) / 'chapter.md'
            source_path.write_text('', encoding='utf-8')

            exact = image_utils.process_images_in_content(
                '![diagram](diagram.png)',
                book_dir,
                output_dir,
                [],
                os.fspath(source_path),
                figure_placement='H',
            )
            compatible = image_utils.process_images_in_content(
                '![diagram](diagram.png)',
                book_dir,
                output_dir,
                [],
                os.fspath(source_path),
                figure_placement='htbp',
            )

            self.assertIn(r'\begin{figure}[H]', exact)
            self.assertIn(r'\begin{figure}[htbp]', compatible)
            self.assertIn(r'height=0.85\textheight,keepaspectratio', compatible)


if __name__ == '__main__':
    unittest.main()
