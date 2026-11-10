package com.portal.conductor;

import java.io.File;
import java.io.IOException;
import java.io.RandomAccessFile;
import java.util.ArrayList;
import java.util.List;

/**
 * v3.43: turns the picture of an MP4 by editing the 9 numbers of the video track matrix ("tkhd" box).
 * Nothing is re-encoded, so it takes a moment even for a 1.4 GB file. Used by the "girar 180" button when a video came out upside down.
 * Only the four matrices that MediaRecorder writes (0, 90, 180, 270 degrees) are understood; anything else is left untouched.
 */
final class Mp4Rotate {
    private Mp4Rotate() {}

    private static final int ONE = 0x00010000, W = 0x40000000;
    private static final int MOOV = 0x6D6F6F76, TRAK = 0x7472616B, TKHD = 0x746B6864;
    /** matrices for 0, 90, 180 and 270 degrees clockwise (the same ones Android's MPEG4Writer writes) */
    static final int[][] M = {
        { ONE, 0, 0, 0, ONE, 0, 0, 0, W },
        { 0, ONE, 0, -ONE, 0, 0, 0, 0, W },
        { -ONE, 0, 0, 0, -ONE, 0, 0, 0, W },
        { 0, -ONE, 0, ONE, 0, 0, 0, 0, W }
    };

    /** position of a video track matrix in the file and the turn (0..3 quarter turns) it holds now */
    private static final class Spot {
        final long pos;
        final int turn;
        Spot(long pos, int turn) { this.pos = pos; this.turn = turn; }
    }

    /** Adds {@code add} degrees (90, 180 or 270) to the picture turn of every video track. Returns the new turn in degrees, or -1 when the file cannot be edited (nothing is written then). */
    static int rotate(File f, int add) {
        if (f == null || add % 90 != 0) return -1;
        int q = (((add / 90) % 4) + 4) % 4;
        RandomAccessFile r = null;
        try {
            r = new RandomAccessFile(f, "rw");
            List<Spot> spots = new ArrayList<Spot>();
            walk(r, 0L, r.length(), 0, spots);
            if (spots.isEmpty()) return -1;
            for (int i = 0; i < spots.size(); i++) if (spots.get(i).turn < 0) return -1;   // a matrix we do not know: do not touch the file
            int result = -1;
            for (int i = 0; i < spots.size(); i++) {
                Spot s = spots.get(i);
                int nt = (s.turn + q) % 4;
                r.seek(s.pos);
                for (int k = 0; k < 9; k++) r.writeInt(M[nt][k]);
                if (i == 0) result = nt * 90;
            }
            return result;
        } catch (IOException e) {
            return -1;
        } catch (RuntimeException e) {
            return -1;
        } finally {
            if (r != null) { try { r.close(); } catch (IOException e) { } }
        }
    }

    /** current picture turn in degrees of the first video track, or -1 */
    static int turnOf(File f) {
        RandomAccessFile r = null;
        try {
            r = new RandomAccessFile(f, "r");
            List<Spot> spots = new ArrayList<Spot>();
            walk(r, 0L, r.length(), 0, spots);
            if (spots.isEmpty() || spots.get(0).turn < 0) return -1;
            return spots.get(0).turn * 90;
        } catch (IOException e) {
            return -1;
        } finally {
            if (r != null) { try { r.close(); } catch (IOException e) { } }
        }
    }

    private static void walk(RandomAccessFile r, long start, long end, int depth, List<Spot> out) throws IOException {
        long pos = start;
        while (pos + 8 <= end) {
            r.seek(pos);
            long size = r.readInt() & 0xFFFFFFFFL;
            int type = r.readInt();
            long hdr = 8;
            if (size == 1) { size = r.readLong(); hdr = 16; }
            else if (size == 0) size = end - pos;
            if (size < hdr || pos + size > end) return;             // damaged: stop reading here
            if ((type == MOOV || type == TRAK) && depth < 4) {
                walk(r, pos + hdr, pos + size, depth + 1, out);
            } else if (type == TKHD) {
                Spot s = readTkhd(r, pos + hdr, size - hdr);
                if (s != null) out.add(s);
            }
            pos += size;
        }
    }

    /** payload of a track header; returns null for tracks without a picture (sound) and for headers too short to understand */
    private static Spot readTkhd(RandomAccessFile r, long p, long len) throws IOException {
        if (len < 4) return null;
        r.seek(p);
        int version = r.readUnsignedByte();
        long mOff = version == 1 ? 52 : 40;
        long need = mOff + 36 + 8;
        if (len < need) return null;
        r.seek(p + mOff + 36);
        int w = r.readInt(), h = r.readInt();
        if (w == 0 || h == 0) return null;                          // sound track
        r.seek(p + mOff);
        int[] m = new int[9];
        for (int k = 0; k < 9; k++) m[k] = r.readInt();
        int turn = -1;
        for (int t = 0; t < 4; t++) {
            boolean same = true;
            for (int k = 0; k < 9; k++) if (M[t][k] != m[k]) { same = false; break; }
            if (same) { turn = t; break; }
        }
        return new Spot(p + mOff, turn);
    }
}
