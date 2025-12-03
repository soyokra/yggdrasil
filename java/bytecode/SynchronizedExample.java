package java.bytecode;

/**
 * 同步示例 - 演示synchronized方法
 */
public class SynchronizedExample {
    
    private int counter = 0;
    
    // synchronized实例方法
    public synchronized void synchronizedMethod() {
        counter++;
        System.out.println("synchronizedMethod(): counter = " + counter);
    }
    
    // synchronized静态方法
    public static synchronized void synchronizedStaticMethod() {
        System.out.println("synchronizedStaticMethod()");
    }
    
    // 同步代码块
    public void synchronizedBlock() {
        synchronized (this) {
            counter++;
            System.out.println("synchronizedBlock(): counter = " + counter);
        }
    }
    
    public int getCounter() {
        return counter;
    }
}

