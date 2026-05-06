################################################################
#
# $Id:$
#
# $Log:$
#
CC=  gcc  # gcc or g++

# [SPECTRAL] 1997 linuxdoom-1.10 has many 32-bit-isms baked in
# (pointer-truncation in WAD overlay structs, sign-extended ints stored
# back as pointers, the renderer's column / sprite / visplane data
# layouts). Rather than port the renderer to 64-bit (the entire reason
# Chocolate Doom and PrBoom+ exist), build the engine in 32-bit mode.
# Requires multilib: `sudo apt install gcc-multilib libc6-dev-i386
# libx11-dev:i386 libxext-dev:i386 libnsl-dev:i386`.
CFLAGS=-g -Wall -m32 -DNORMALUNIX -DLINUX # -DUSEASM
LDFLAGS=-m32 -L/usr/X11R6/lib
# Dropped -lnsl: the i_net.c BSD sockets path uses libc directly, and
# the 1997 link line's `-lnsl` is for SunRPC / NIS calls that the
# engine never actually invokes. libnsl:i386 isn't installed by
# default on Ubuntu multilib, and we don't need it.
LIBS=-lXext -lX11 -lm

# subdirectory for objects
O=linux

# not too sophisticated dependency
OBJS=				\
		$(O)/doom_spectral.o		\
		$(O)/doomdef.o		\
		$(O)/doomstat.o		\
		$(O)/dstrings.o		\
		$(O)/i_system.o		\
		$(O)/i_sound.o		\
		$(O)/i_video.o		\
		$(O)/i_net.o			\
		$(O)/tables.o			\
		$(O)/f_finale.o		\
		$(O)/f_wipe.o 		\
		$(O)/d_main.o			\
		$(O)/d_net.o			\
		$(O)/d_items.o		\
		$(O)/g_game.o			\
		$(O)/m_menu.o			\
		$(O)/m_misc.o			\
		$(O)/m_argv.o  		\
		$(O)/m_bbox.o			\
		$(O)/m_fixed.o		\
		$(O)/m_swap.o			\
		$(O)/m_cheat.o		\
		$(O)/m_random.o		\
		$(O)/am_map.o			\
		$(O)/p_ceilng.o		\
		$(O)/p_doors.o		\
		$(O)/p_enemy.o		\
		$(O)/p_floor.o		\
		$(O)/p_inter.o		\
		$(O)/p_lights.o		\
		$(O)/p_map.o			\
		$(O)/p_maputl.o		\
		$(O)/p_plats.o		\
		$(O)/p_pspr.o			\
		$(O)/p_setup.o		\
		$(O)/p_sight.o		\
		$(O)/p_spec.o			\
		$(O)/p_switch.o		\
		$(O)/p_mobj.o			\
		$(O)/p_telept.o		\
		$(O)/p_tick.o			\
		$(O)/p_saveg.o		\
		$(O)/p_user.o			\
		$(O)/r_bsp.o			\
		$(O)/r_data.o			\
		$(O)/r_draw.o			\
		$(O)/r_main.o			\
		$(O)/r_plane.o		\
		$(O)/r_segs.o			\
		$(O)/r_sky.o			\
		$(O)/r_things.o		\
		$(O)/w_wad.o			\
		$(O)/wi_stuff.o		\
		$(O)/v_video.o		\
		$(O)/st_lib.o			\
		$(O)/st_stuff.o		\
		$(O)/hu_stuff.o		\
		$(O)/hu_lib.o			\
		$(O)/s_sound.o		\
		$(O)/z_zone.o			\
		$(O)/info.o				\
		$(O)/sounds.o

all:	 $(O)/linuxxdoom

clean:
	rm -f *.o *~ *.flc
	rm -f linux/*

$(O)/linuxxdoom:	$(OBJS) $(O)/i_main.o
	$(CC) $(CFLAGS) $(LDFLAGS) $(OBJS) $(O)/i_main.o \
	-o $(O)/linuxxdoom $(LIBS)

$(O)/%.o:	%.c
	$(CC) $(CFLAGS) -c $< -o $@

#############################################################
#
#############################################################