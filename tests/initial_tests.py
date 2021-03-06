import unittest
from unittest.mock import patch

import context
from fisfeed.prep import map_ids

class TestFISIdMethods(unittest.TestCase):

	def test_validate_shortid(self):
		good_shortid = 'sghj177'
		data = [ good_shortid ]
		id_idx = 0
		self.assertEqual( map_ids.validate_shortid(data, id_idx), data )

		bad_shortid = '@@@@@'
		data = [ bad_shortid ]
		id_idx = 0
		out = map_ids.validate_shortid(data, id_idx)
		self.assertNotEqual( out, data )
		self.assertEqual( out[id_idx], None )
		self.assertNotEqual( out, [ None ] )
		self.assertEqual( out, ( None, ) )

	def test_validate_bruid(self):
		good_bruid = '123456789'
		data = ( good_bruid, )
		id_idx = 0
		self.assertEqual( map_ids.validate_bruid(data, id_idx), data )

		bad_bruid = '12345678'
		data = [ bad_bruid ]
		id_idx = 0
		out = map_ids.validate_bruid(data, id_idx)
		self.assertNotEqual( out, data )
		self.assertIsInstance( out, map_ids.Invalid )
		with self.assertRaises( TypeError ):
			out[id_idx]
		self.assertEqual( out.log_info, bad_bruid)

	def test_id_picker(self):
		data = [ 0, 'a', 1, 'b', 2 ]
		id_mapping = { 1 : 0, 3: 1 }
		out = map_ids.id_picker( data, id_mapping )
		self.assertEqual( out, ('a', 'b') )
		self.assertEqual( out[ id_mapping[data.index('a')] ], 'a')
		self.assertEqual( out[ id_mapping[data.index('b')] ], 'b')
		self.assertEqual( len(out), len(id_mapping) )

	@patch('fisfeed.logging')
	def test_pull_ids(self, mock_log):
		sample_data = [
			[ '000000006','aroddam','000004','Roddom','Alfonse' ],
			[ '000000008','yazwan','000003', 'Azwan','Yusef'],
			[ '000000002','rsimos','000002','Simos','Rhonda'],
			[ '000000009','papapoiadam','007700','Papadeou','Stavros'],
			[ '020000','jamruss','300000','Russel','Jamarcus'],
			[ '000000001','', '000001' 'Johnson','Don'],
			[ '000000007','', '000007' 'Thomas','Philip Michael']
		]
		idxs = { 'BRUID': 0, 'SHORTID' : 1}
		out = map_ids.pull_ids(sample_data, idxs)
		self.assertIn( ('000000008','yazwan'), out )
		self.assertIn( ('000000009', None), out )
		self.assertIn( ('000000007', None), out)
		self.assertNotIn( ('020000','jamruss'), out )		

	@patch('fisfeed.logging')
	def test_update_id_map(self, mock_log):
		sample_data = [
			[ '000000006','aroddam' ],
			[ '000000008','yazwan' ],
			[ '000000002','rsimos' ],
			[ '000000001', None ],
			[ '000000007', None ],
			[ '000000000', None ],
			[ '000000017', 'lazarus' ]
		]
		idxs = { 'BRUID': 0, 'SHORTID' : 1}
		sample_map = {	'000000006' : 'aroddam',
						'000000001' : 'johnsond',
						'000000008' : 'azkaban',
						'000000017'	: None,
						'000000000'	: None }
		out = map_ids.update_id_map(sample_data, sample_map)
		self.assertIn('000000002', out)
		self.assertEqual(out['000000008'], 'azkaban')
		self.assertEqual(out['000000001'], 'johnsond')
		self.assertEqual(out['000000007'], None)
		self.assertEqual(out['000000000'], False)
		self.assertEqual(out['000000017'], 'lazarus')

		empty_map = {}
		out = map_ids.update_id_map(sample_data, empty_map)
		self.assertEqual(out, { k:v for k,v in sample_data })

if __name__ == '__main__':
	unittest.main()