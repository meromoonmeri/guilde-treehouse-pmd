import unittest
import numpy as np
from PIL import Image
from source.tera_v2.prismatic import glass,sheet,PHASES

class GlassTests(unittest.TestCase):
    def sample(self):
        a=np.zeros((17,21,4),dtype=np.uint8);a[:,:,:3]=[10,20,30]
        a[3:15,5:18]=[45,160,210,255];a[2,6]=[70,90,120,90]
        return Image.fromarray(a)
    def test_alpha_and_transparent_rgb_preserved(self):
        im=self.sample();original=np.array(im)
        for p in range(PHASES):
            out=np.array(glass(im,p))
            self.assertTrue(np.array_equal(original[:,:,3],out[:,:,3]))
            self.assertTrue(np.array_equal(original[original[:,:,3]==0],out[original[:,:,3]==0]))
        self.assertTrue(np.array_equal(original,np.array(im)))
    def test_real_change_and_periodic_closure(self):
        im=self.sample()
        self.assertFalse(np.array_equal(np.array(glass(im,0)),np.array(glass(im,6))))
        self.assertTrue(np.array_equal(np.array(glass(im,0)),np.array(glass(im,PHASES))))
        self.assertTrue(np.array_equal(np.array(glass(im,-1)),np.array(glass(im,PHASES-1))))
    def test_empty_and_single_pixel_inputs(self):
        for size in [(1,1),(1,9),(9,1),(16,16)]:
            for alpha in [0,128,255]:
                im=Image.new('RGBA',size,(90,150,200,alpha));out=glass(im,4)
                self.assertEqual(out.size,size)
                self.assertTrue(np.all(np.array(out)[:,:,3]==alpha))
    def test_cells_do_not_sample_neighbors(self):
        left=self.sample();right=Image.new('RGBA',left.size,(220,45,35,255))
        im=Image.new('RGBA',(left.width*2,left.height));im.paste(left,(0,0));im.paste(right,(left.width,0))
        out=sheet(im,left.size,7)
        self.assertTrue(np.array_equal(np.array(out.crop((0,0,left.width,left.height))),np.array(glass(left,7))))
    def test_fully_opaque_cell_stays_finite_and_colored(self):
        im=Image.new('RGBA',(12,14),(120,170,210,255))
        with np.errstate(all='raise'):
            out=np.array(glass(im,3))
        self.assertTrue(np.all(out[:,:,:3]>0))

    def test_invalid_geometry_blocked(self):
        with self.assertRaises(ValueError):sheet(self.sample(),(8,8),0)
        with self.assertRaises(ValueError):sheet(self.sample(),(0,8),0)

if __name__=='__main__':unittest.main()
