package java.bytecode;

/**
 * 可变参数示例 - 演示可变参数方法
 */
public class VarargsExample {
    
    // 可变参数示例
    public void varargsExample(String... args) {
        for (String arg : args) {
            System.out.println(arg);
        }
    }
    
    // 可变参数与其他参数组合
    public void varargsWithOtherParams(String prefix, int... numbers) {
        System.out.println("Prefix: " + prefix);
        for (int num : numbers) {
            System.out.println(num);
        }
    }
    
    // 可变参数 - 数组形式
    public void varargsArrayExample(int[] numbers) {
        for (int num : numbers) {
            System.out.println(num);
        }
    }
}

