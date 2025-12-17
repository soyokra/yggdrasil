package com.yggdrasil.learn.classloader;

import java.io.File;

public class BootstrapClassLoaderTest {
    public static void main(String[] args) {
        // 获取Bootstrap ClassLoader的加载路径（系统属性）
        String bootClassPath = System.getProperty("sun.boot.class.path");
        // 按系统路径分隔符拆分（Windows是;，Linux/Mac是:）
        String[] paths = bootClassPath.split(File.pathSeparator);

        System.out.println("Bootstrap ClassLoader 加载路径：");
        for (String path : paths) {
            System.out.println(path);
        }
    }
}
