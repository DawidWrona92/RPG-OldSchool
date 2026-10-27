"""Refresh package SHA-256 metadata after intentional changes; run from any cwd.
The manifest excludes itself (circular hash), caches and this program's live process state.
"""
from pathlib import Path
import hashlib,json,platform
from PIL import Image
import PIL,numpy,scipy
root=Path(__file__).resolve().parents[1]
mesh=Path('/tmp/hero-base.obj')
assert mesh.is_file(),'Read pinned CC0 OBJ into /tmp/hero-base.obj first.'
files=[]
for path in sorted(root.rglob('*')):
    if not path.is_file() or '__pycache__' in path.parts or path.name=='manifest.json':continue
    rel=path.relative_to(root).as_posix()
    e={'file':rel,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'status':'PROTOTYPE_NOT_APPROVED'}
    if path.suffix=='.png':
        im=Image.open(path);im.load();e.update(resolution=list(im.size),channels=im.mode,bit_depth=path.read_bytes()[24])
    else:e.update(resolution=None,channels=None,bit_depth=None)
    if path.name.startswith('hero_eye_'):
        e.update(map='iris_basecolor' if 'iris' in path.name else 'sclera_basecolor',color_space='sRGB',method='Reused byte-for-byte from existing repository branch after decoding, dimension and visual checks; generator/model undocumented.',tools=['Unknown original tool; audited with Pillow 12.3.0 and NumPy 2.3.5'],models=None,sources=[{'repository':'DawidWrona92/RPG-OldSchool','commit':'59966fbb59ef87f685dd6ef67bed5b8d0e540144','path':'assets/textures/characters/hero/unique/'+path.name}])
    elif path.name.startswith('hero_skin_body_'):
        name=path.stem.removeprefix('hero_skin_body_').removesuffix('_2048')
        methods={
            'basecolor':'Procedural unlit pigment material at native UV-interpolated surface positions: tanning, regional redness, lips, scalp, follicles, hand dirt and nails; no illumination/AO input.',
            'roughness':'Anatomical scalar material response with T-zone, cheeks, lips, scalp, stubble, hands, keratin and pore variation; not inferred from albedo luminance.',
            'height':'16-bit linear scalar microrelief: pores, forehead/crowfeet/nasolabial creases, hand lines and lip cracks. Neutral 0.5; proposed full range 0.002 m; no high-poly sculpt.',
            'normal_opengl':'Normalized tangent-space RGB vectors from height gradient; +Y OpenGL (UV V increases upward). Used with Blender MikkTSpace normal mapping. Not a sculpt bake.',
            'sss_mask':'Relative anatomical thinness proxy: brighter ears, nose and fingers. Not a measured thickness/radius map.'}
        method=methods[name]
        if '_2048' in path.stem:method+=' 2K derived from 4K by Lanczos; tangent vectors renormalized after filtering.'
        e.update(map=name,color_space='sRGB' if name=='basecolor' else 'linear / Non-Color',method=method,tools=['CPython '+platform.python_version(),'NumPy '+numpy.__version__,'SciPy '+scipy.__version__,'Pillow '+PIL.__version__],models=None,sources=['source/build_maps.py','MakeHuman hm08 CC0, group body, native UV; pinned mesh below','docs/koncepty/17-bohater-i-woz.jpg (palette/character reference only)','docs/art/characters/tekstury-bohatera/BRIEF-TEKSTURY.md'])
    elif rel.startswith('podglad/skin_'):
        e.update(map='diagnostic_render',color_space='sRGB / AgX',method='Blender Cycles render from current body maps, unchanged CC0 body group, diagnostic orthographic closeup; no final hair, eyeballs or clothes.',tools=['Blender 4.3.2 / Cycles / 64 samples / seed 1703 / 4 threads'],models=['MakeHuman hm08 body'],sources=['source/render_check.py','current hero_skin_body_*.png','pinned mesh below'])
    else:
        e.update(map='validation_report' if rel.startswith('qa/') else 'documentation' if path.suffix=='.md' else 'source_script',color_space='not applicable',method='Authored package documentation, reproducible technical generation or validation.',tools=['Codex'],models=None,sources=['repository brief and references'])
    files.append(e)
manifest={'schema_version':1,'status':'PROTOTYPE_NOT_APPROVED','scope':'Part A only; ten skin maps plus two retained eye maps and diagnostic/support files','repository':'DawidWrona92/RPG-OldSchool','branch':'vibe/hero-textures-gpt6','main_base_commit':'9bf3ff94dfa62aad057594425f4f4bf2b0a44208','previous_work_commit':'744b42bb0c33fb379715889c7c779b8c68a12764','mesh':{'repository':'DawidWrona92/RPG-OldSchool','commit':'421c7e895e6a029181dcb7c63ab277ad7bab4ca0','path':'assets/sprites/player/source/third_party/base.obj','group':'body','license':'CC0 (MakeHuman hm08 header)','sha256':hashlib.sha256(mesh.read_bytes()).hexdigest()},'normal_convention':'Tangent OpenGL +Y; Blender MikkTSpace basis; no high-poly bake','height_convention':{'neutral':0.5,'suggested_full_range_meters':0.002},'padding':'Nearest-surface full-background dilation; microdetail fades 32–56 px from UV boundary','ai_image_attempt':'image_gen face-UV painting trial was rejected for production alignment; none of its pixels are used in the delivered maps. No external photographs used. Eye generator remains undocumented.','manifest_self_hash':'Excluded to avoid circular hashing. Every other delivered file is listed.','files':files}
(root/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print(f'Manifest written: {len(files)} files.')
