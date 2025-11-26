# mybatis Mapper接口源码分析

## 使用示例

mybatis的一个简单使用示例：

1. 定义XML映射
```xml
<mapper namespace="com.sprival.UserMapper">
    <select id="selectUser" parameterType="int" resultType="User">
        SELECT * FROM users WHERE id = #{id}
    </select>
</mapper>
```

2. 定义接口

```java
public interface UserMapper {
    User selectUser(int id);
}
```

3. 执行查询
```
class Test {
    public static void main(String[] args) {
        // 1. 从 XML 配置构建 SqlSessionFactory
        String resource = "mybatis-config.xml";
        InputStream inputStream = Resources.getResourceAsStream(resource);
        SqlSessionFactory sqlSessionFactory = new SqlSessionFactoryBuilder().build(inputStream);

        // 2. 获取 SqlSession 并执行 SQL
        try (SqlSession session = sqlSessionFactory.openSession()) {
            UserMapper mapper = session.getMapper(UserMapper.class);
            User user = mapper.selectUser(1);
        } catch(Exception e) {
            e.printStackTrace();
        }
    }
}
```


## MapperProxy

我们定义的UserMapper是一个接口，那么通过``` UserMapper mapper = session.getMapper(UserMapper.class)```
获取到的实现是什么呢？
mybatis负责mapper实例化的类如下：
- MapperRegistry：MapperProxyFactory的注册缓存
- MapperProxyFactory：创建MapperProxy实例
- MapperProxy：动态代理Mapper接口
- MapperMethod：将Mapper面向业务的方法转换为操作数据库的方法

```
MapperRegistry -> MapperProxyFactory -> MapperProxy -> MapperMethod
```

mybatis通过JDK动态代理的方式为Mapper接口创建了代理实现MapperProxy，MapperProxy的invoke方法又将具体实现逻辑交由MapperMethod进行处理

此处为示例代码，用于演示实现原理，方便理解，实际逻辑可以查看源码文件

### 接口
```
public interface UserMapper {
    String queryUser(String id);
}
```

### 代理
```
public class MapperProxy implements InvocationHandler {
     @Override
    public Object invoke(Object proxy, Method method, Object[] args) throws Throwable {
       // 转为mapperMethod处理
       mapperMethod.execute(sqlSession, args);
    }
}
```

### 生成动态代理对象
```
UserMapper userMapper = (UserMapper) Proxy.newProxyInstance(UserMapper.class.getClassLoader(), new Class[] { UserMapper.class }, mapperProxy);
userMapper.queryUser("10028301010"); // 实际调用 MapperProxy.invoke 方法。
```

## MapperScan
集成到Spring的时候，除了SqlSession bean注册，一个关键点是如何将用户定义的Mapper接口
mybatis负责mapperScan的类如下：
- MapperScan
- MapperScannerRegistrar
- MapperScannerConfigurer
- MapperFactoryBean
- ClassPathMapperScanner

主要的调用链路如下，MapperScan扫描包目录下的文件，用MapperFactoryBean注册为BeanClass，通过getObject()转到SqlSessionTemplate.getMapper()。
最终回到MapperRegistry.getMapper()，MapperProxy代理实现
```text
@MapperScan("com.soyokra.sprival.dao.*.mapper")
=> MapperScan @Import({MapperScannerRegistrar.class})：注册MapperScannerRegistrar
=> MapperScannerRegistrar.registerBeanDefinitions：设置MapperScannerConfigurer属性的basePackage为com.soyokra.sprival.dao.*.mapper
=> MapperScannerConfigurer.postProcessBeanDefinitionRegistry
=> ClassPathMapperScanner.processBeanDefinitions：扫描basePackage生成BeanDefinition，并且设置BeanClass为MapperFactoryBean
=> Mapper注册为Bean的时候，通过MapperFactoryBean的getObject()转到了SqlSessionTemplate.getMapper()
=> SqlSessionTemplate.getMapper()方法最终调用到MapperRegistry.getMapper()
```