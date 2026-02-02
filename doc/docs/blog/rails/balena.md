# Host Computer & OS

## Overview

`Rails49` runs well on a small computer like a [Raspberry Pi](https://www.raspberrypi.com/) or an [NUC](https://de.wikipedia.org/wiki/Next_Unit_of_Computing).

What operating system should we use? As the project consists of several rather independent components, it would be attractive to have a decicated computer for each to avoid conflicts and the hard to diagnose problem: "it worked last week, my only change was to a totally unrelated program".

So-called "container operating systems" address this issue by providing an an environment that to each component looks like a dedicated computer. It is the same technology that is used for running cloud infrastructure such as Google Search.

Fortunately we do not need an entire datacenter to achieve this. Virtually all operating systems allow installation of container runtimes such as [docker](https://www.docker.com/) or [podman](https://podman.io/). An even simpler approach is to use a "bare bones" operating system which provides only the features needed to run containers. Forging support e.g. for a graphical user interface both simplifies the setup and reduces hardware requirements. 

Good (free) choices for small installations such as `Rails49` include [balenaOS](https://www.balena.io/os/) or [Fedora IoT](https://fedoraproject.org/iot/).

`Rails49` will run just fine on either, or with any standard container runtime including docker or podman installed on MacOS or Windows. 

Here we choose balenaOS for its simplicity and ease of use. But if you already have or are familiar with another container platform, you can use that instead.


## BalenaOS

To get started with balenaOS, create an account on [balena.io](https://balena.io/os). 

Login and click "Create a Fleet". Give your fleet a name (e.g. `rails49`) and choose the correct image for your device (e.g. `Raspberry Pi 4 (using 64bit OS)`). 

You will be presented with a new page showing the fleet you just created and the suggestion to add a device. Click "Add Device". Change "Edition" to "Development". If you want to access your device via wifi (rather than E   thernet), click "Wifi + Ethernet" under the Network section and enter the SSID and password for your network.

Click "Flash". You will be asked to download and open the balenaEtcher application. Insert a micro SD card into your computer and choose it as the target in balenaEtcher. Then click "Flash!". 

Transfer the SD card to your Raspberry Pi. In a few minutes the device should appear in your balena.io dashboard.

## Release App

* `balena push <fleet-name>` (Recommended): Pushes local code to balenaCloud, where it is built and deployed.
* `balena deploy <fleet-name>`: Deploys previously built images to a fleet.
* `git push balena master`: Deploys code changes using git.