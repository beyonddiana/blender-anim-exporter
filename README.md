# Blender Plugin for exporting Second Life animations

## Why a .anim exporter?

If you create your animations with Avastar or Bento Buddy, you do NOT need this plugin, because Avastar and Bento Buddy have already everything for exporting to .anim. But if:

- if you create your animations in plain blender (without Avastar and without Bento Buddy)
- if you create your animations in some other softwares then want to import then SL as .anim format

then this plugin could help you!

Personally, i make my animations either in Cascadeur 3D, or in Rokoko Studio. It is not possible to export in a custom format with these softwares. So i export my anims from Cascadeur or from Rokoko to some standard format (fbx, bvh, etc), import them in Blender, then export them to .anim with this plugin. Another solution would be to retarget the anim to either Avastar or Bento Buddy rigs, but 1/ it takes time and 2/ not everybody has these add-ons.


Credits:
I've used a lot from the blender source code itself, especially the bvh exporter, that i've used as a base for collecting data about the animation. I've also reused from code from https://github.com/FelixWolf/SecondLifeTools/blob/master/animjson for writting the anim file and json file.

## How to install?

Go to the Releases page: https://github.com/aglaia-resident/blender-anim-exporter/releases  
In the latest release, download the file blender-sl-anim-exporter.zip  
This zip file is the plugin.

Then install it as any other plugin:
- In Blender, go to Edit > Preferences > Add-ons
- Click Install
- Select the zip file  that you have downloaded
- Then don't forget to tick the checkbox to enable it.

Now if you go to File > Export, you should see a new option "Second Life Animation (.anim)"

## What model to use?

Your model can come from another software, as long as it respects the SL rig bones hierarchy.

If you don't have any model yet, you need a rig for creating your animation. You can use the Avatar Workbench that is available for free:
https://www.avalab.org/avatar-workbench/

For starting, you can also use the simple rig and mesh that i provide on google drive:
https://drive.google.com/drive/folders/1gXWxunKk8z1QulD1lHNPzbZ1Y9TMfUPq
Donwload avatar.blend and open it in Blender.

I've made this rig from the Avatar Workbench. I removed all bones except the body ones, so you get the torso, neck, head, arms and legs.
If you want to animate bento bones and volume bones, then please use the avatar workbench.

## IMPORTANT REQUIREMENTS

Should work with Blender 3.0 and upper.

1/ At least 2 frames in the animation

Please make sure that your animation has at least 2 frames. Only 1 frame won't work. This is something that i will correct later. If you want to make a static pose, then duplicate the first frame into the second frame.

2/ Orientation of the model

In Blender, your model must face you when you are in front view. Type 1 on the numpad to go in front view: the model look at you.

Indeed, the orientation of an avatar in SL is facing X. But in Blender, the convention is to have the avatar facing -Y, which means facing you in front view. It makes the use of mirror tools easier. So i've followed the Blender convention.

Make sure the avatar is facing you in front view, and check that its orientation is 0,0,0. If not, select the armature and tick Object > Apply > Rotation

![alt text](https://i.gyazo.com/caa192e79f0e157a1aae735f9dcaad9f.png)

### Keyframe your locations and/or rotations properly

The exporter will export all the location and rotation channels that are in your dopesheet. So it is your job to make the dopesheet clean. Most of the time, you will want rotation + location for mPelvis, and rotation only for all other bones.

I've decided to not include a checkbox "rotation only" in the exporter, as some other plugins do, because i find this confusing: even when checked, that usually still exports mPelvis locations. Instead, i think it is better to have a clean dopesheet with only the channels that you want to export.

## How to use?

Create your animation. Remember that it must be at least 2 frames. Only one frame will not work.

If you have several actions in your blender file: select the one you want to export in the Dopesheet > Action Editor.

Then select the armature and go to File > Export > Second Life Animation 

Here are some options. If you don't see the options on the right, click the Cog icon:

![alt text](https://i.gyazo.com/7cdda64345839c836efc06b5a01f1d5c.png)

Options :

- Priority: choose between 0 to 6
- Loop: tick this box if your animation should run in loop
- If loop: set which frame is the first frame of the loop
- Ease in duration
- Ease out duration 
- Dump as JSON : this is for debug purpose. If you want to analyze your animation, this file could help you. You can open it with any text editor, like notepad.

Other settings that are not in the Export widget, but have to be set right in Blender:

The first and last frame will be the ones that are defined in your timeline:

![alt text](https://i.gyazo.com/99bd95e2c123143835f59a551b2866a1.png)

The FPS is defined in Blender as well :

![alt text](https://i.gyazo.com/484305ccd49333ab27c94d9ffd02f150.png)

## KNOWN ISSUES

In some rare and random cases, after an export, the model gets rotated by 90 degrees around Z. If this happens, please re-rotate it correctly by typing R Z -90 then Object > Apply Rotation.
