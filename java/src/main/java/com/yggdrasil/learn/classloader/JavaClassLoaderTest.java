package com.yggdrasil.learn.classloader;

public class JavaClassLoaderTest {
    public static void main(String[] args) {
        ClassLoader loader = JavaClassLoaderTest.class.getClassLoader();
    }
}
