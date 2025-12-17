package com.yggdrasil.learn.classloader;

public class ClassLoaderTest {
    public static void main(String[] args) {
        // 1. 查看核心类（String）的加载器：启动类加载器（输出null，因为是C++实现）
        ClassLoader stringClassLoader = String.class.getClassLoader();
        System.out.println("String类的加载器：" + stringClassLoader);

        // 2. 查看扩展类（如javax.crypto.Cipher）的加载器：扩展类加载器
        ClassLoader extClassLoader = javax.crypto.Cipher.class.getClassLoader();
        System.out.println("扩展类的加载器：" + extClassLoader);

        // 3. 查看自定义类的加载器：应用程序类加载器
        ClassLoader appClassLoader = ClassLoaderTest.class.getClassLoader();
        System.out.println("自定义类的加载器：" + appClassLoader);

        // 4. 查看应用程序类加载器的父加载器：扩展类加载器
        System.out.println("应用程序加载器的父加载器：" + appClassLoader.getParent());

        // 5. 查看扩展类加载器的父加载器：启动类加载器（输出null）
        System.out.println("扩展类加载器的父加载器：" + appClassLoader.getParent().getParent());
    }
}
