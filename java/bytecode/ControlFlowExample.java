package java.bytecode;

/**
 * 控制流示例 - 演示if-else、switch、for循环、while循环、增强for循环
 */
public class ControlFlowExample {
    
    // if-else示例
    public void ifElseExample(int value) {
        if (value > 0) {
            System.out.println("Positive");
        } else if (value < 0) {
            System.out.println("Negative");
        } else {
            System.out.println("Zero");
        }
    }
    
    // switch示例
    public void switchExample(int value) {
        switch (value) {
            case 1:
                System.out.println("One");
                break;
            case 2:
                System.out.println("Two");
                break;
            default:
                System.out.println("Other");
        }
    }
    
    // for循环示例
    public void forLoopExample() {
        for (int i = 0; i < 10; i++) {
            System.out.println(i);
        }
    }
    
    // 增强for循环示例
    public void enhancedForLoopExample(String[] array) {
        for (String item : array) {
            System.out.println(item);
        }
    }
    
    // while循环示例
    public void whileLoopExample() {
        int i = 0;
        while (i < 10) {
            System.out.println(i);
            i++;
        }
    }
}

