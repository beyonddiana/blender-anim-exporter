# Blender Plugin for exporting Second Life animations

## WHY A .ANIM EXPORTER?

If you create your animations with Avastar or Bento Buddy, you do NOT need this plugin, because Avastar and Bento Buddy have already everything for exporting to .anim. But if:

- if you create your animations in plain blender (without Avastar and without Bento Buddy)
- if you create your animations in some other softwares then want to import then SL as .anim format

then this plugin could help you!

Personally, i make my animations either in Cascadeur 3D, or in Rokoko Studio. It is not possible to export in a custom format with these softwares. So i export my anims from Cascadeur or from Rokoko to some standard format (fbx, bvh, etc), import them in Blender, then export them to .anim with this plugin. Another solution would be to retarget the anim to either Avastar or Bento Buddy rigs, but 1/ it takes time and 2/ not everybody has these add-ons.


Credits:
I've used a lot from the blender source code itself, especially the bvh exporter, that i've used as a base for collecting data about the animation. I've also reused from code from https://github.com/FelixWolf/SecondLifeTools/blob/master/animjson for writting the anim file and json file.

## HOW TO INSTALL?

Go to the Releases page: https://github.com/aglaia-resident/blender-anim-exporter/releases  
In the latest release, download the file blender-sl-anim-exporter.zip  
This zip file is the plugin.

Then install it as any other plugin:
- In Blender, go to Edit > Preferences > Add-ons
- Click Install
- Select the zip file  that you have downloaded
- Then don't forget to tick the checkbox to enable it.

Now if you go to File > Export, you should see a new option "Second Life Animation (.anim)"

## WHAT MODEL TO USE?

Your model can come from another software, as long as it respects the SL rig bones hierarchy.

If you don't have any model yet, you need a rig for creating your animation. You can use the Avatar Workbench that is available for free:
https://www.avalab.org/avatar-workbench/

For starting, you can also use the simple rig and mesh that i provide on google drive:  
https://drive.google.com/drive/folders/1gXWxunKk8z1QulD1lHNPzbZ1Y9TMfUPq  
Donwload avatar.blend and open it in Blender. IT REQUIRES BLENDER 3.0 OR UPPER

I've made this rig from the Avatar Workbench. I removed all bones except the body ones, so you get the torso, neck, head, arms and legs.
If you want to animate bento bones and volume bones, then please use the avatar workbench.

## ORIENTATION OF THE MODEL

In Blender, your model must face you when you are in front view. Type 1 on the numpad to go in front view: the model look at you.

Indeed, the orientation of an avatar in SL is facing X. But in Blender, the convention is to have the avatar facing -Y, which means facing you in front view. It makes the use of mirror tools easier. So i've followed the Blender convention.

Make sure the avatar is facing you in front view, and check that its orientation is 0,0,0. If not, select the armature and tick Object > Apply > Rotation

![alt text](https://i.gyazo.com/caa192e79f0e157a1aae735f9dcaad9f.png)

## HOW TO USE?

Create your animation.

If you have several actions in your blender file: select the one you want to export in the Dopesheet > Action Editor.

Then select the armature and go to File > Export > Second Life Animation 

Here are some options. If you don't see the options on the right, click the Cog icon:

![alt text](https://i.gyazo.com/7a3772498945f1e82e16fdec4ec8c562.png)

## OPTIONS

**- Start frame, End frame, FPS**: these settings cannot be changed here. Indeed, they come from your blender scene itself. You can change Start frame and End frame in the timline:

![alt text](https://i.gyazo.com/99bd95e2c123143835f59a551b2866a1.png)

And you can change the FPS in the Output Properties panel:

![alt text](https://i.gyazo.com/484305ccd49333ab27c94d9ffd02f150.png)

**- Export Translations**: Most of the time, in SL, you want to animate bones by rotation + translation for mPelvis, and rotation only for all other bones. If you check this box, all existing translation channels will be exported. If you don't check it (which is the default), only mPelvis translation will be exported, and all other bones translations will be ignored. If you are unsure, do not check it.

**- Priority**: choose between 0 and 6

**- Loop**: tick this box if your animation should run in loop

**- Looop starts at frame**: sets which frame is the first frame of the loop. This has no effect if you didn't check the "Loop?" checkbox.

**- Ease in** and **Ease out **

**- Dump as JSON** : this is for debug purpose. If you want to analyze your animation, this file could help you. You can open it with any text editor, like notepad.

## KNOWN ISSUES

In some rare and random cases, after an export, the model gets rotated by 90 degrees around Z. If this happens, please re-rotate it correctly by typing R Z -90 then Object > Apply Rotation.
