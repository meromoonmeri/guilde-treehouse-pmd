import hashlib
import json
import unittest
import numpy as np
from PIL import Image
from source.pokemon_custom.politoed_portraits_v1.build import key_magenta,native_subject,expression_mask,NATIVE,OUT,PRESERVE
from source.pmd_character_pipeline.make_prompt import make


class MagentaWorkflowTests(unittest.TestCase):
    def test_key_preserves_real_pink_cheek(self):
        im=Image.new('RGBA',(2,1));im.putpixel((0,0),(255,0,255,255));im.putpixel((1,0),(222,160,207,255))
        result,_=key_magenta(im)
        self.assertEqual(result.getpixel((0,0)),(0,0,0,0))
        self.assertEqual(result.getpixel((1,0)),(222,160,207,255))

    def test_cream_iris_is_not_erased_with_background(self):
        normal=Image.open(NATIVE/'Normal.png').convert('RGBA');a=np.array(normal);s=np.array(native_subject(normal))
        iris=np.zeros((40,40),bool);iris[11:18,12:20]=True
        iris &= np.all(a[:,:,:3]==(228,243,185),axis=2)
        self.assertTrue(iris.any());self.assertTrue(np.all(s[iris,3]==255))

    def test_existing_native_files_unchanged(self):
        for emotion in PRESERVE:
            self.assertEqual((NATIVE/f'{emotion}.png').read_bytes(),(OUT/'portraits_individual'/f'{emotion}.png').read_bytes())

    def test_new_composites_and_anatomy(self):
        normal=native_subject(Image.open(NATIVE/'Normal.png'));a=np.array(normal);fg=a[:,:,3]>0;mask=expression_mask()&fg
        report=json.loads((OUT/'verification.json').read_text())
        count=0
        for emotion,r in report['portraits'].items():
            if r.get('existing_native_preserved'):continue
            subject=np.array(Image.open(OUT/'editable'/f'{emotion}_subject.png').convert('RGBA'))
            bg=np.array(Image.open(OUT/'editable'/f'{emotion}_canonical_background.png').convert('RGBA'))
            final=Image.open(OUT/'portraits_individual'/f'{emotion}.png').convert('RGBA');f=np.array(final)
            self.assertTrue(np.array_equal(subject[~mask],a[~mask]))
            self.assertTrue(np.array_equal(f[~fg],bg[~fg]))
            self.assertLessEqual(len(final.getcolors(9999)),15)
            self.assertTrue(np.all(f[:,:,3]==255));count+=1
        self.assertEqual(count,10)
        self.assertEqual(report['missing_required'],['Sigh','Stunned'])

    def test_prompt_distinguishes_generation_and_composite(self):
        brief={'species':'Politoed','spritecollab_slot':'0186','references':['normal.png'],'normal_portrait_reference':'normal.png'}
        p=make(brief,'portrait','Happy')
        self.assertIn('#FF00FF MAGENTA',p)
        self.assertIn('POSTPROCESSING ONLY',p)
        self.assertIn('NEVER draw a second smile',p)
        self.assertNotIn('no magenta or transparent holes',p)


if __name__=='__main__':unittest.main()
