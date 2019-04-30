---
title: Box Software Cloning
---

# Box Software Cloning

These instructions are for developers who wish to clone an existing ATLeS box
Raspberry Pi installation to create a new base OS image for installing on new
boxes.

## Making a New Image

To save a disk image of a working/configured Raspberry Pi SD card:

[TODO: Could simplify to `dd` plus an automated script using loopback, https://github.com/Drewsif/PiShrink, and some of the steps below.]

1. Put card into card reader in a Linux machine.

2. (Optional) Use the `dist/prep_image.sh` script to remove unneeded files from
   the card before cloning.

3. Unmount the partitions if auto-mounted (Ubuntu auto-mounts them)

       $ sudo umount /dev/[device of auto-mounted partition[s]]

4. (Optional) Use `gparted` to shrink the root partition on the card to just
   the used space plus a small buffer.  (E.g., with 2.20GiB used, `resize2fs`
   wouldn't let me make it 2500MiB, but 3000MiB was okay.)

5. (Optional) Zero unused blocks in the root partition so the disk image can be
   compressed more.  Requires the `zerofree` utility.  If `/dev/sdc2` is the
   root partition:

       $ sudo zerofree -v /dev/sdc2

6. Determine the number of blocks now occupied.
   (Adapted from: [http://raspberrypi.stackexchange.com/a/8314](http://raspberrypi.stackexchange.com/a/8314))

       $ sudo fdisk -l /dev/[device of entire card (e.g., sdd)]
   
   Prints the partition table.

   Record 'End' of the final partition and the sector size.

7. Use `dd` to create the image using the size from the previous step.
    
       $ sudo dd bs=[sector size] count=[end of final partition + 1] if=/dev/[device of entire card] of=atles_rpi_`date +%Y%m%d`.img status=progress

