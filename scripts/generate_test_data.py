import os
import suite2p 
import shutil
import numpy as np 

from pathlib import Path
from conftest import initialize_ops #Guarantees that tests and this script use the same ops
from tests.regression.utils import FullPipelineTestUtils, DetectionTestUtils, ExtractionTestUtils
from suite2p.extraction import masks

"""
IMPORTANT: When running this script, make sure to use it in the scripts directory 
(e.g., suite2p/scripts). The generated test data will be placed in the directory 
suite2p/scripts/test_data. Take the directories in this folder and replace the directories 
with the same name in suite2p/data/test_data (e.g.,replace suite2p/data/test_data/1plane1chan1500 with suite2p/scripts/test_data/1plane1chan1500). 
"""

current_dir = Path(os.getcwd())
# Assumes the input file has already been downloaded
test_input_dir_path = current_dir.parent.joinpath('data')
# Output directory where suite2p results are kept
test_data_dir_path =  current_dir.joinpath('test_data')

class GenerateFullPipelineTestData:
	# Full Pipeline Tests
	def generate_1p1c1500_expected_data(ops):
		"""
		Generates expected output for test_1plane_1chan_with_batches_metrics_and_exported_to_nwb_format
		for test_full_pipeline.py
		"""
		test_ops = FullPipelineTestUtils.initialize_ops_test1plane_1chan_with_batches(ops.copy())
		suite2p.run_s2p(ops=test_ops)
		rename_output_dir('1plane1chan1500')

	# def generate_1p2c_expected_data(ops):
	#   """
	#   Generates expected output for test_1plane_2chan_sourcery of test_full_pipeline.py.
	#   """
	#   test_ops = FullPipelineTestUtils.initialize_ops_test_1plane_2chan_sourcery(ops.copy())
	#   suite2p.run_s2p(ops=test_ops)
	#   rename_output_dir('1plane2chan')

	def generate_2p2c1500_expected_data(ops):
		"""
		Generates expected output for test_2plane_2chan_with_batches of test_full_pipeline.py.
		"""
		test_ops = FullPipelineTestUtils.initialize_ops_test2plane_2chan_with_batches(ops.copy())
		suite2p.run_s2p(ops=test_ops)
		rename_output_dir('2plane2chan1500')

	def generate_2p2zmesoscan_expected_data(ops):
		"""
		Generates expected output for test_mesoscan_2plane_2z of test_full_pipeline.py.
		"""
		test_ops = FullPipelineTestUtils.initialize_ops_test_mesoscan_2plane_2z(ops.copy())
		suite2p.run_s2p(ops=test_ops)
		rename_output_dir('mesoscan')

	def generate_all_data(full_ops):
		# Expected Data for test_full_pipeline.py
		GenerateFullPipelineTestData.generate_1p1c1500_expected_data(full_ops)
		# generate_1p2c_expected_data(ops)
		GenerateFullPipelineTestData.generate_2p2c1500_expected_data(full_ops)
		GenerateFullPipelineTestData.generate_2p2zmesoscan_expected_data(full_ops)

class GenerateDetectionTestData:
	# Detection Tests
	def generate_detection_1plane1chan_test_data(ops):
		"""
		Generates expected output for test_detection_output_1plane1chan of test_detection_pipeline.py.
		"""
		# Use only the smaller input tif
		ops.update({
			'tiff_list': ['input.tif'],
		})
		ops = DetectionTestUtils.prepare(
			ops,
			[[Path(ops['data_path'][0]).joinpath('detection/pre_registered.npy')]],
			(404, 360)
		)
		ops, stat = suite2p.detection.detect(ops[0])
		ops['neuropil_extract'] = True
		cell_masks, neuropil_masks = masks.create_masks(stat, ops['Ly'], ops['Lx'], ops=ops)
		output_dict = {
			'stat': stat,
			'cell_masks': cell_masks,
			'neuropil_masks': neuropil_masks
		}
		np.save('expected_detect_output_1p1c0.npy', output_dict)
		# Remove suite2p directory generated by prepare function
		shutil.rmtree(os.path.join(test_data_dir_path, 'suite2p'))

	def generate_detection_2plane2chan_test_data(ops):
		"""
		Generates expected output for test_detection_output_2plane2chan of test_detection_pipeline.py.
		"""
		ops.update({
			'tiff_list': ['input.tif'],
		})
		ops.update({
			'nchannels': 2,
			'nplanes': 2,
		})
		detection_dir = Path(ops['data_path'][0]).joinpath('detection')
		two_plane_ops = DetectionTestUtils.prepare(
			ops,
			[
				[detection_dir.joinpath('pre_registered01.npy'), detection_dir.joinpath('pre_registered02.npy')],
				[detection_dir.joinpath('pre_registered11.npy'), detection_dir.joinpath('pre_registered12.npy')]
			]
			, (404, 360),
		)
		two_plane_ops[0]['meanImg_chan2'] = np.load(detection_dir.joinpath('meanImg_chan2p0.npy'))
		two_plane_ops[1]['meanImg_chan2'] = np.load(detection_dir.joinpath('meanImg_chan2p1.npy'))
		for i in range(len(two_plane_ops)):
			op = two_plane_ops[i]
			# Neuropil_masks are later needed for extraction test data step
			op['neuropil_extract'] = True
			op, stat = suite2p.detection.detect(ops=op)
			cell_masks, neuropil_masks = masks.create_masks(stat, op['Ly'], op['Lx'], ops=op)
			output_dict = {
				'stat': stat,
				'cell_masks': cell_masks,
				'neuropil_masks': neuropil_masks
			}
			np.save('expected_detect_output_%ip%ic%i.npy' % (ops['nchannels'], ops['nplanes'], i), output_dict)
		# Get rid of registered binary files that were created for detection module in 
		# DetectionTestUtils.prepare
		remove_binary_file(test_data_dir_path, 0, '')
		remove_binary_file(test_data_dir_path, 0, '_chan2')
		remove_binary_file(test_data_dir_path, 1, '')
		remove_binary_file(test_data_dir_path, 1, '_chan2')
	
	def generate_all_data(ops):
		GenerateDetectionTestData.generate_detection_1plane1chan_test_data(ops)
		GenerateDetectionTestData.generate_detection_2plane2chan_test_data(ops)
		rename_output_dir('detection')
		# Move over expected outputs into detection
		shutil.move('expected_detect_output_1p1c0.npy', test_data_dir_path.joinpath('detection'))
		shutil.move('expected_detect_output_2p2c0.npy', test_data_dir_path.joinpath('detection'))
		shutil.move('expected_detect_output_2p2c1.npy', test_data_dir_path.joinpath('detection'))

class GenerateClassificationTestData:
	# Classification Tests
	def generate_classification_test_data(ops):
		stat = np.load(test_input_dir_path.joinpath('test_inputs/classification/pre_stat.npy'), allow_pickle=True)
		iscell = suite2p.classification.classify(stat, classfile=suite2p.classification.builtin_classfile)
		np.save(str(test_data_dir_path.joinpath('classification').joinpath('expected_classify_output_1p1c0.npy')), iscell)

	def generate_all_data(ops):
		make_new_dir(test_data_dir_path.joinpath('classification'))
		GenerateClassificationTestData.generate_classification_test_data(ops)

class GenerateExtractionTestData:
	# Extraction Tests
	def generate_preprocess_baseline_test_data(ops):
		# Relies on full pipeline test data generation being completed
		f = np.load(test_data_dir_path.joinpath('1plane1chan1500/suite2p/plane0/F.npy'))
		baseline_vals = ['maximin', 'constant', 'constant_prctile']
		for bv in baseline_vals:
			pre_f = suite2p.extraction.preprocess(
				F=f,
				baseline=bv,
				win_baseline=ops['win_baseline'],
				sig_baseline=ops['sig_baseline'],
				fs=ops['fs'],
				prctile_baseline=ops['prctile_baseline']
			)
			np.save(str(test_data_dir_path.joinpath('extraction/{}_f.npy'.format(bv))), pre_f)

	def generate_extraction_output_1plane1chan(ops):
		ops.update({
			'tiff_list': ['input.tif'],
		})
		ops = ExtractionTestUtils.prepare(
			ops,
			[[Path(ops['data_path'][0]).joinpath('detection/pre_registered.npy')]],
			(404, 360)
		)
		op = ops[0]
		extract_input = np.load(
			str(test_data_dir_path.joinpath('detection/expected_detect_output_1p1c0.npy')),
			allow_pickle=True
		)[()]
		extract_helper(op, extract_input, 0)
		remove_binary_file(test_data_dir_path, 0, '')
		os.rename(os.path.join(test_data_dir_path, 'suite2p'), os.path.join(test_data_dir_path, '1plane1chan'))
		shutil.move(os.path.join(test_data_dir_path, '1plane1chan'), os.path.join(test_data_dir_path, 'extraction'))

	def generate_extraction_output_2plane2chan(ops):
		ops.update({
			'nchannels': 2,
			'nplanes': 2,
			'tiff_list': ['input.tif'],
		})
		# Create multiple ops for multiple plane extraction
		ops = ExtractionTestUtils.prepare(
			ops,
			[
				[Path(ops['data_path'][0]).joinpath('detection/pre_registered01.npy'), 
				Path(ops['data_path'][0]).joinpath('detection/pre_registered02.npy')],
				[Path(ops['data_path'][0]).joinpath('detection/pre_registered11.npy'), 
				Path(ops['data_path'][0]).joinpath('detection/pre_registered12.npy')]
			]
			, (404, 360),
		)
		ops[0]['meanImg_chan2'] = np.load(Path(ops[0]['data_path'][0]).joinpath('detection/meanImg_chan2p0.npy'))
		ops[1]['meanImg_chan2'] = np.load(Path(ops[1]['data_path'][0]).joinpath('detection/meanImg_chan2p1.npy'))
		# 2 separate inputs for each plane (but use outputs of detection generate function)
		extract_inputs = [
			np.load(
				str(test_data_dir_path.joinpath('detection/expected_detect_output_2p2c0.npy')),allow_pickle=True
			)[()],
			np.load(
				str(test_data_dir_path.joinpath('detection/expected_detect_output_2p2c1.npy')),allow_pickle=True
			)[()],
		] 
		for i in range(len(ops)):
			extract_helper(ops[i], extract_inputs[i], i)
			# Assumes second channel binary file is present
			remove_binary_file(test_data_dir_path, i, '')
			remove_binary_file(test_data_dir_path, i, '_chan2')
		os.rename(os.path.join(test_data_dir_path, 'suite2p'), os.path.join(test_data_dir_path, '2plane2chan'))
		shutil.move(os.path.join(test_data_dir_path, '2plane2chan'), os.path.join(test_data_dir_path, 'extraction'))

	def generate_all_data(ops):
		make_new_dir(test_data_dir_path.joinpath('extraction'))
		GenerateExtractionTestData.generate_preprocess_baseline_test_data(ops)
		GenerateExtractionTestData.generate_extraction_output_1plane1chan(ops)
		GenerateExtractionTestData.generate_extraction_output_2plane2chan(ops)

def extract_helper(ops, extract_input, plane):
	plane_dir = Path(ops['save_path0']).joinpath(f'suite2p/plane{plane}')
	print(plane_dir)
	plane_dir.mkdir(exist_ok=True, parents=True)
	stat, F, Fneu, F_chan2, Fneu_chan2 = suite2p.extraction.create_masks_and_extract(
		ops,
		extract_input['stat'],
		extract_input['cell_masks'],
		extract_input['neuropil_masks']
	)
	dF = F - ops['neucoeff'] * Fneu
	dF = suite2p.extraction.preprocess(
		F=dF,
		baseline=ops['baseline'],
		win_baseline=ops['win_baseline'],
		sig_baseline=ops['sig_baseline'],
		fs=ops['fs'],
		prctile_baseline=ops['prctile_baseline']
	)
	spks = suite2p.extraction.oasis(F=dF, batch_size=ops['batch_size'], tau=ops['tau'], fs=ops['fs'])
	np.save(plane_dir.joinpath('ops.npy'), ops)
	np.save(plane_dir.joinpath('stat.npy'), stat)
	np.save(plane_dir.joinpath('F.npy'), F)
	np.save(plane_dir.joinpath('Fneu.npy'), Fneu)
	np.save(plane_dir.joinpath('F_chan2.npy'), F_chan2)
	np.save(plane_dir.joinpath('Fneu_chan2.npy'), Fneu_chan2)
	np.save(plane_dir.joinpath('spks.npy'), spks)

def rename_output_dir(new_dir_name):
	curr_dir_path = os.path.abspath(os.getcwd())
	new_dir_path = os.path.join(test_data_dir_path, new_dir_name)
	if os.path.exists(new_dir_path):
		shutil.rmtree(new_dir_path)
	os.makedirs(new_dir_path)
	shutil.move(os.path.join(test_data_dir_path, 'suite2p'), new_dir_path)

def make_new_dir(new_dir_name):
	if not os.path.exists(new_dir_name):
		os.makedirs(new_dir_name)
		print('Created test directory at ' + str(new_dir_name))

def remove_binary_file(dir_path, plane_num, bin_file_suffix):
	os.remove(os.path.join(dir_path, 'suite2p/plane{}/data{}.bin'.format(plane_num, bin_file_suffix)))

def main():
	#Create test_data directory if necessary
	make_new_dir(test_data_dir_path)
	full_ops = initialize_ops(test_data_dir_path, test_input_dir_path)
	GenerateFullPipelineTestData.generate_all_data(full_ops)
	det_ops = initialize_ops(test_data_dir_path, test_input_dir_path)
	GenerateDetectionTestData.generate_all_data(det_ops)
	GenerateClassificationTestData.generate_all_data(full_ops)
	GenerateExtractionTestData.generate_all_data(full_ops)
	return 

if __name__ == '__main__':
	main()
