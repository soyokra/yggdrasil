package com.yggdrasil.learn.stack;

public class StackTest {
    public static void main(String[] args) {
        StackTest stackTest = new StackTest();
        stackTest.run(3);
    }

    public int run(int d) {
        int a = 1;
        int b = 2;
        int c = a + b;
        int f = add(c, d);
        return f;
    }

    public int add(int a, int b) {
        return a + b;
    }
}
