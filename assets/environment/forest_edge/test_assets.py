"""Basic checks for generated first-pass assets; not a game integration test."""
import json
import unittest
from pathlib import Path
from PIL import Image

DIR=Path(__file__).resolve().parent/'output'

class Tests(unittest.TestCase):
    def setUp(self):
        self.doc=json.loads((DIR/'scene.json').read_text(encoding='utf8'))
    def test_schema(self):
        self.assertEqual(self.doc['projection']['camera_elevation_degrees'],30)
        self.assertEqual(self.doc['projection']['pixels_per_meter'],60)
        self.assertGreaterEqual(len(self.doc['objects']),15)
        self.assertEqual(len({o['id'] for o in self.doc['objects']}),len(self.doc['objects']))
    def test_scene_size(self):
        for name in ['scene_preview.png','scene_ground.png']:
            im=Image.open(DIR/name)
            self.assertEqual(im.size,(1536,900))
    def test_material_seams(self):
        for mat in ['forest_floor','mud','stone','moss']:
            for channel in ['albedo','normal','roughness','height']:
                im=Image.open(DIR/'materials'/f'{mat}_{channel}.png')
                self.assertEqual(im.size,(256,256))
                self.assertEqual(list(im.crop((0,0,256,1)).getdata()),list(im.crop((0,255,256,256)).getdata()))
                self.assertEqual(list(im.crop((0,0,1,256)).getdata()),list(im.crop((255,0,256,256)).getdata()))
    def test_transparent_props(self):
        for key,obj in self.doc['props_catalog'].items():
            im=Image.open(DIR/obj['file']);self.assertEqual(im.mode,'RGBA');self.assertTrue(im.getchannel('A').getbbox(),key)
            self.assertEqual(obj['dimensions_px'],list(im.size))
            self.assertGreaterEqual(obj['anchor_px'][0],0)
    def test_collision_data(self):
        for o in self.doc['objects']:
            self.assertIn(o['type'],self.doc['props_catalog'])
            self.assertGreaterEqual(o['collision_radius_m'],0)
            self.assertEqual(len(o['world_m']),2)

if __name__ == '__main__':unittest.main()
